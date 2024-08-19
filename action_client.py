import spacy
import requests
from user_data import user_data,config,keywords,facture_data,facture_keywords
from spacy.lang.fr.stop_words import STOP_WORDS as fr_stop_words
from spacy.lang.en.stop_words import STOP_WORDS as en_stop_words
from chatbot_client import closest_tag,load_qa
file_path = "tag.json"
qa_data = load_qa(file_path)
nlp_fr = spacy.load('fr_core_news_md')  # Charger le modèle français de spaCy
nlp_en = spacy.load('en_core_web_md')

def choisir_tableau(user_input):
    tab_keyword = {}
    tab_user_data = {}
    tag = closest_tag(user_input, qa_data, "fr")
    print("tag",tag)
    if tag == "creation client":
        tab_keyword = keywords.copy()
        tab_user_data = user_data.copy()
    elif tag == "creation facture":
        tab_keyword = facture_keywords.copy()
        tab_user_data = facture_data.copy()
    return tab_keyword, tab_user_data




def add_client(user_data, api_url, static_token):

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Authorization": f"Bearer {static_token}"
    }
    #url = api_url.format(id=user_data['id'])
        
        # Ajouter un nouveau client en utilisant les données de user_data
    response = requests.post(api_url, json=user_data, headers=headers)
        
    if response.status_code == 200:
            print("Client ajouté avec succès.")
            # Gérer d'autres actions en cas de succès, si nécessaire
    else:
            print(f"Erreur lors de l'ajout du client: {response.status_code}")
            print(f"Message d'erreur : {response.json()}")


def add_facture(user_data, api_url, static_token):
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Authorization": f"Bearer {static_token}"
    }
    #url = api_url.format(id=user_data['id'])
        
        # Ajouter un nouveau client en utilisant les données de user_data
    response = requests.post(api_url, json=user_data, headers=headers)
        
    if response.status_code == 200:
            print("facture ajouté avec succès.")
            # Gérer d'autres actions en cas de succès, si nécessaire
    else:
            print(f"Erreur lors de l'ajout du facture: {response.status_code}")
            print(f"Message d'erreur : {response.json()}")
 
    



# Fonction pour détecter l'information dans le message utilisateur
def detect_information(user_input, tab_keyword, tab_user_data):
    user_input_lower = user_input.lower()
    detected_info = {}
    
    # Obtenir les tableaux appropriés
    print(tab_keyword,tab_user_data)
    for key, aliases in tab_keyword.items():
        for alias in aliases:
            if alias in user_input_lower:
                value = extract_value(user_input_lower, alias)
                if value:
                    detected_info[key] = value

    if not detected_info:
        # Si aucune information n'est détectée directement, chercher la clé la plus proche par similarité
        closest_key = get_closest_cle(user_input_lower, tab_keyword)
        print("closest", closest_key)
        if closest_key:
            detected_info[closest_key] = extract_value(user_input_lower, tab_keyword)

    if detected_info:
        for key, value in detected_info.items():
            if key in config and isinstance(config[key], tuple) and len(config[key]) > 2 and value in config[key][2]:
                tab_user_data[key] = config[key][2][value]
            else:
                tab_user_data[key] = value
        
        print("Données utilisateur mises à jour:", tab_user_data)
        return detected_info

    return None
   

# Fonction pour trouver la clé la plus proche par similarité
def get_closest_cle(user_input, tab_keyword):
    threshold = 0.7
    best_similarity = 0.0
    closest_question = None

    user_input_doc = nlp_fr(user_input)

    # Comparaison de similarité pour chaque mot-clé
    for question in tab_keyword.keys():
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
    for key in keywords:
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