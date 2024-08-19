import spacy
import requests
from user_data import facture_data,config,facture_keywords,values_key
from spacy.lang.fr.stop_words import STOP_WORDS as fr_stop_words
from spacy.lang.en.stop_words import STOP_WORDS as en_stop_words


nlp_fr = spacy.load('fr_core_news_md')  # Charger le modèle français de spaCy
nlp_en = spacy.load('en_core_web_md')


def add_facture(facture_data, api_url, static_token):
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Authorization": f"Bearer {static_token}"
    }
    

    response = requests.post(api_url, json=facture_data
    , headers=headers)
        
    if response.status_code == 200:
            print("facture ajouté avec succès.")
            # Gérer d'autres actions en cas de succès, si nécessaire
    else:
            print(f"Erreur lors de l'ajout de facture: {response.status_code}")
            print(f"Message d'erreur : {response.json()}")
    
 
    



# Fonction pour détecter l'information dans le message utilisateur
def detect_information(user_input):
    user_input_lower = user_input.lower()
    detected_info = {}

    for key, aliases in facture_keywords.items():
        for alias in aliases:
            if alias in user_input_lower:
                print(alias)
                value = extract_value(user_input_lower, alias)
                if value:
                    detected_info[key] = value
                    print(detected_info)
    if not detected_info:
        # Si aucune information n'est détectée directement, chercher la clé la plus proche par similarité
        closest_key = get_closest_cle(user_input_lower, facture_keywords)
        print("closest",closest_key)
        if closest_key:
            detected_info[closest_key] = extract_value(user_input_lower, facture_keywords[closest_key][0])

    if detected_info:
         
         for key, value in detected_info.items():
            if key in config and isinstance(config[key], tuple) and len(config[key]) > 2 and value in config[key][2]:
                print(key)
            else:             
                print('hey',detected_info)
         return detected_info

    return None

# Fonction pour trouver la clé la plus proche par similarité
def get_closest_cle(user_input, keywords):
    threshold=0.7
    best_similarity = 0.0
    closest_question = None

    user_input_doc = nlp_fr(user_input)

    # Comparaison de similarité pour chaque mot-clé
    for question in keywords.keys():
        question_doc = nlp_fr(question)
        similarity = user_input_doc.similarity(question_doc)
        if similarity > best_similarity:
            best_similarity = similarity
            closest_question = question

    # Retourner le mot-clé le plus similaire si la similarité dépasse le seuil
    if best_similarity >= threshold:
        return closest_question
    else:
        return None

# Fonction pour extraire la valeur après un mot-clé dans le message utilisateur
def extract_value(message, keyword):
    start_index = message.find(keyword) + len(keyword) + 1
    end_index = message.find('.', start_index)
    
    # Cherche le prochain mot-clé pour limiter la portée de la valeur extraite
    next_keyword_index = len(message)
    for key in values_key:
        if key != keyword and key in message:
            key_index = message.find(key)
            if start_index < key_index < next_keyword_index:
                next_keyword_index = key_index
    
    if end_index == -1 or end_index > next_keyword_index:
        end_index = next_keyword_index
    
    return message[start_index:end_index].strip()


def preprocess_text(text, language):
    if language == 'fr':
        doc = nlp_fr(text.lower())
        tokens = [token.text for token in doc if not token.is_punct and not token.is_space and token.text not in fr_stop_words]
    elif language == 'en':
        doc = nlp_en(text.lower())
        tokens = [token.text for token in doc if not token.is_punct and not token.is_space and token.text not in en_stop_words]
    else:
        doc = nlp_fr(text.lower())  # Default to French if language is not supported
        tokens = [token.text for token in doc if not token.is_punct and not token.is_space and token.text not in fr_stop_words]
    
    return ' '.join(tokens)



def ajouter_option(champ, option):
    token, api_url, options = config[champ]
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Authorization": f"Bearer {token}"
    }
    url = f"{api_url}?type={option}"  # Correction ici pour concaténer correctement l'URL avec l'option
    payload = {
            "@id": "/api/societe/{champ}",
            "@type": champ,
            "libelle": option,
            "estPredefini": True,
            "estDefault": False,
            "estDesactive": False
    }
        
    try:
        response = requests.post(url, json=payload, headers=headers)  # Utilisation de `url` au lieu de `api_url` ici
        if response.status_code == 201:
            print(f"Nouvelle option '{option}' ajoutée avec succès à la plateforme.")
            print(f"Réponse de l'API : {response.json()}")
          
            return response.json().get('@id')
        else:
            print(f"Erreur lors de l'ajout de l'option '{option}' à la plateforme: {response.status_code}")
            print(f"Message d'erreur : {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Erreur de requête lors de l'ajout de l'option '{option}' à la plateforme: {str(e)}")

def extract_clients_info(nom_client, adresse_client, token="eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpYXQiOjE3MjA2MjU2NDcsImV4cCI6MTcyMDY2MTY0Nywicm9sZXMiOlsiUk9MRV9BRE1JTiJdLCJzY2hlbWFBY3RpdmUiOiJnZXN0aW9uX3ByZXByb2RfMTRfMDYiLCJjb21wYW55IjpbeyJub20iOiJFVEMiLCJjb2RlIjoiQ09MSSIsImFjdGl2ZSI6ZmFsc2V9LHsibm9tIjoiU09MQVZJVEUiLCJjb2RlIjoiU09MQSIsImFjdGl2ZSI6dHJ1ZX1dLCJub20iOiJhbGljZSIsInVzZXJuYW1lIjoiYWxpY2V2MkBldGNpbmZvLmZyIiwic29jaWV0ZSI6MX0.PMtxf0wsn1fgikUeLA4Cn21-fI4L_HvSKLtwdJYE4Pz7DnLckA--dPcZzcuWszlp-L33WE2POe--9TEDmZwe8oZA9nNDmEKlTA0Ek8B-NLW2j4pBkwkv3tm2PMeqS3YOGosFf8i7ypdXUvRiCbQ7FNJNZZ9cAOW-oTGENadaU_HRx3zj44JrBH89PAnghljJtgy2nEj18qf2zOMzrrSxYBN42EgbYlqlKwIxjPOqtpnXC48w_8qWx285i3sls-px2ZEcR4AtCrktaEl0zzb50F15YH-gfRdW40fxHS4eDTqidZu77_1rWu842R3XQLddad9RGdc_4_EsSYYjEFMuvg"):
    url = 'https://pp-unum-back.etcinfo.tech/api/societe/clients'  # URL de votre API pour obtenir les clients
    headers = {
        'Authorization': f'Bearer {token}'  # Insérez ici votre méthode d'authentification et token
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Gère les erreurs HTTP
        clients = response.json()['hydra:member']  # Accès aux membres de la réponse JSON
        filtered_clients = []

        for client in clients:
            if 'nom' in client and 'adresses' in client:
                if client['nom'].lower() == nom_client.lower():
                    for adresse in client['adresses']:
                        if 'adresse' in adresse and adresse['adresse'].lower() == adresse_client.lower():
                            filtered_clients.append({
                                'id': client.get('id'),
                                'nom': client.get('nom'),
                                'adresse': adresse.get('adresse'),
                                'code': client.get('code')
                            })
        print(filtered_clients)
        print(len(filtered_clients))
        return filtered_clients

    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la requête API : {str(e)}")
        return []