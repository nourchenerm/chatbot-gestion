

from flask import Flask, request, jsonify, session
from flask_cors import CORS
import secrets
from chatbot_client import load_qa, chatbot_logic, closest_tag

from action_client import preprocess_text,add_client,detect_information,ajouter_option,choisir_tableau,add_facture

from user_data import user_data,config
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Clé secrète pour les sessions
CORS(app)

# File path for the intents JSON file
file_path = "tag.json"

# Load initial QA data from the JSON file
qa_data = load_qa(file_path)
tag2 = [] 
@app.route('/client', methods=['POST'])
def chatbot_client():
    message = request.json['message']
    user_input = preprocess_text(message, "fr")
    # Récupérer le contexte de la session ou l'initialiser
    context = session.get('context', 'initial')
    pending_additions = session.get('pending_additions', {})
    tag1 = closest_tag(user_input, qa_data, "fr")
    tag2.append(tag1)
    print(tag2[0])
    # Obtenir les tableaux appropriés
    tab_keyword, tab_user_data = choisir_tableau(user_input)
    
    if context == 'initial' and tag1 != 'confirmer':
        detected_info = detect_information(user_input, tab_keyword, tab_user_data)
        
        if detected_info:
            additions_to_ask = {}
            
            for detected_type, detected_value in detected_info.items():
                if detected_type in config and detected_value not in config[detected_type][2]:
                    additions_to_ask[detected_type] = detected_value

            if additions_to_ask:
                response = {
                    'response': f"Les informations suivantes n'existent pas : " + ', '.join([f"{k} : {v}" for k, v in additions_to_ask.items()]) + ". Voulez-vous les ajouter ? (oui/non)",
                    'context': 'awaiting_confirmation',
                    'pending_additions': additions_to_ask,
                    'user_data': {key: value for key, value in tab_user_data.items() if value is not None}
                }
                session['context'] = 'awaiting_confirmation'
                session['pending_additions'] = additions_to_ask
                return jsonify(response)
            else:
                response = {
                    'response': "Toutes les informations détectées sont déjà présentes. Voulez-vous ajouter autre chose ? si non taper confirmer ",
                    'context': 'initial',
                     'pending_additions': additions_to_ask,
                    'user_data': {key: value for key, value in tab_user_data.items() if value is not None}
                }
                session['context'] = 'initial'
                return jsonify(response)
        else:
            answer = chatbot_logic(user_input, qa_data, "fr")
            print(answer)
            response = {
                'response': answer,
                'context': 'initial',
                'user_data': {key: value for key, value in tab_user_data.items() if value is not None}
            }
            session['context'] = 'initial'
            return jsonify(response)

    elif context == 'awaiting_confirmation':
        tag = closest_tag(user_input, qa_data, "fr")
        
        if tag == "oui":
            for item_type, item_value in pending_additions.items():
                id = ajouter_option(item_type, item_value)
                tab_user_data[item_type] = id
            response = {
                'response': "Les informations suivantes ont été ajoutées avec succès : " + ', '.join([f"{k} : {v}" for k, v in pending_additions.items()]) + ". Voulez-vous ajouter autre chose ? si non taper confirmer",
                'context': 'initial',
                'user_data': {key: value for key, value in tab_user_data.items() if value is not None},
                'item_value': item_value,
                'pending': pending_additions
            }
            session['context'] = 'initial'
            session['pending_additions'] = {}
            return jsonify(response)
        elif tag == "non":
            for item_type, item_value in pending_additions.items():
                tab_user_data[item_type] = {
                    '@id': '/api/societe/forme-juridiques/10',
                    '@type': 'FormeJuridique',
                    'id': 10,
                    'codeInsee': None,
                    'libelle': None,
                    'typeForme': 2,  # Remplacez avec le type de forme juridique approprié si nécessaire
                    'estPredefini': False,  # Modifiez selon vos besoins
                    'estDefault': False,  # Modifiez selon vos besoins
                    'estDesactive': False  # Modifiez selon vos besoins
                }
            response = {
                'response': "D'accord, l'ajout de nouvelles informations est annulé. Voulez-vous ajouter autre chose ? si non taper confirmer ",
                'context': 'initial',
                'user_data': {key: value for key, value in tab_user_data.items() if value is not None}
            }
            session['context'] = 'initial'
            session['pending_additions'] = {}
            return jsonify(response)
        else:
            response = {
                'response': "Je n'ai pas compris votre réponse. Voulez-vous ajouter les informations mentionnées ? Répondez par 'oui' ou 'non'.",
                'context': 'awaiting_confirmation',
                'pending_additions': pending_additions,
                'user_data': {key: value for key, value in tab_user_data.items() if value is not None}
            }
            return jsonify(response)
        
    elif context == 'initial' and tag1 == "confirmer":
        if tag2[0] =='creation client':
            print("tag2",tag2[0])
            add_client(tab_user_data, api_url="https://pp-unum-back.etcinfo.tech/api/societe/clients", static_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NJ9.eyJpYXQiOjE3MjAxNjc0NDksImV4cCI6MTcyMDIwMzQ0OSwicm9sZXMiOlsiUk9MRV9BRE1JTiJdLCJzY2hlbWFBY3RpdmUiOiJjb2xpYnJpXzE5XzA2IiwiY29tcGFueSI6W3sibm9tIjoiRVRDIiwiY29kZSI6IkNPTEkiLCJhY3RpdmUiOnRydWV9LHsibm9tIjoiU09MQVZJVEUiLCJjb2RlIjoiU09MQSIsImFjdGl2ZSI6ZmFsc2V9XSwibm9tIjoiYWxpY2UiLCJ1c2VybmFtZSI6ImFsaWNldjJAZXRjaW5mby5mciIsInNvY2lldGUiOjF9.aE47b1cGMLduwS-zdeqcZy4WWKPw91wpCRVbjIo-gSJ0aEP1FAPWzfP05voLiEvtRXyqU0HDRaTv0IlJpwmxI8RZ-SuvCZqEI7CL-botdWSu-PTUiFdVW3HsMD0j5REbWRRleVCMBEN2WFLEwglIdXGSJ-vhXoQSEeEt5gy5wuHyxV3Sn_MEsq6dCBNcATshmfvOpT1ZXhM8iJJj7x6RZVcN06L0wJaFc6RmqGpmR05hJwRjH4ShvxGf3QKXIqtl-eh_hjnZ5mLjX66Tn6d2nibG1Pii7GYGIAN4dak41dQnXvD3SVP3hEJEVGXawyhYEknSBHUcUMJr-ayPylDfeA")
            
            response = {
                'response': f"Client ajouté avec succès.",
                'context': 'initial',
                'user_data': {key: value for key, value in tab_user_data.items() if value is not None}
            }
            tag2.clear()
            session['context'] = 'initial'
            session['pending_additions'] = {}
            return jsonify(response)
        elif tag2[0] =="creation facture":
            add_facture(tab_user_data, api_url="https://pp-unum-back.etcinfo.tech/api/societe/clients", static_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJSzI1NiJ9.eyJpYXQiOjE3MjAxNjc0NDksImV4cCI6MTcyMDIwMzQ0OSwicm9sZXMiOlsiUk9MRV9BRE1JTiJdLCJzY2hlbWFBY3RpdmUiOiJjb2xpYnJpXzE5XzA2IiwiY29tcGFueSI6W3sibm9tIjoiRVRDIiwiY29kZSI6IkNPTEkiLCJhY3RpdmUiOnRydWV9LHsibm9tIjoiU09MQVZJVEUiLCJjb2RlIjoiU09MQSIsImFjdGl2ZSI6ZmFsc2V9XSwibm9tIjoiYWxpY2UiLCJ1c2VybmFtZSI6ImFsaWNldjJAZXRjaW5mby5mciIsInNvY2lldGUiOjF9.aE47b1cGMLduwS-zdeqcZy4WWKPw91wpCRVbjIo-gSJ0aEP1FAPWzfP05voLiEvtRXyqU0HDRaTv0IlJpwmxI8RZ-SuvCZqEI7CL-botdWSu-PTUiFdVW3HsMD0j5REbWRRleVCMBEN2WFLEwglIdXGSJ-vhXoQSEeEt5gy5wuHyxV3Sn_MEsq6dCBNcATshmfvOpT1ZXhM8iJJj7x6RZVcN06L0wJaFc6RmqGpmR05hJwRjH4ShvxGf3QKXIqtl-eh_hjnZ5mLjX66Tn6d2nibG1Pii7GYGIAN4dak41dQnXvD3SVP3hEJEVGXawyhYEknSBHUcUMJr-ayPylDfeA")
            
            response = {
                'response': f"facture ajouté avec succès.",
                'context': 'initial',
                'user_data': {key: value for key, value in tab_user_data.items() if value is not None}
            }
            session['context'] = 'initial'
            session['pending_additions'] = {}
            tag2.clear()

            return jsonify(response)
        else :
              return jsonify({'response': 'Invalid request or context.'})

    else:
        response = {
            'response': "Je n'ai pas compris votre demande. Pouvez-vous répéter ?",
            'context': 'initial'
        }
        session['context'] = 'initial'
        session['pending_additions'] = {}

        return jsonify(response)
    
 


if __name__ == '__main__':
    app.run(debug=True)

