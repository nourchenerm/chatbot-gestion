from flask import Flask, request, jsonify, session
from flask_cors import CORS
import secrets
from chatbot_client import load_qa, chatbot_logic, closest_tag

from action_facture import preprocess_text,add_facture,detect_information,ajouter_option,extract_clients_info
from user_data import config,facture_data,facture_keywords
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Clé secrète pour les sessions
CORS(app)

# File path for the intents JSON file
file_path = "tag.json"

# Load initial QA data from the JSON file
qa_data = load_qa(file_path)

@app.route('/facture', methods=['POST'])
def chatbot():
    extract_clients_info("karine", "l@l.com")

    message = request.json['message']
    user_input = preprocess_text(message,"fr")
    # Récupérer le contexte de la session ou l'initialiser
    context = session.get('context', 'initial')
    pending_additions = session.get('pending_additions', {})
    tag1 =closest_tag(user_input, qa_data, "fr")
    clients =[]
    if context == 'initial' and tag1 != 'confirmer':
        detected_info = detect_information(user_input)    
        clients = extract_clients_info(detected_info['tier.nom'], detected_info['adresseFacturation.adresse'],token="vhgh")
        print(detected_info)
        
        if detected_info:
            additions_to_ask = {}
            for client in clients : 
                for detected_type, detected_value in client.items():
                    if detected_type in facture_keywords:
                        keys = detected_type.split('.')
                        print("keys",keys)
                        if len(keys) > 1:
                            if keys[0] in facture_data and isinstance(facture_data[keys[0]], dict):
                                facture_data[keys[0]][keys[1]] = detected_value
                            else:
                                additions_to_ask[detected_type] = detected_value
                        elif detected_type in facture_data:
                            facture_data[detected_type] = detected_value
                        else:
                            additions_to_ask[detected_type] = detected_value
                    

            if additions_to_ask:
                response = {
                    'response': f"Les informations suivantes n'existent pas : " + ', '.join([f"{k} : {v}" for k, v in additions_to_ask.items()]) + ". Voulez-vous les ajouter ? (oui/non)",
                    'context': 'awaiting_confirmation',
                    'pending_additions': additions_to_ask,
                    'facture_data': {key: value for key, value in facture_data.items() if value is not None}
                          }
                session['context'] = 'awaiting_confirmation'
                session['pending_additions'] = additions_to_ask
                return jsonify(response)
            else:
                response = {
                    'response': "Toutes les informations détectées sont déjà présentes. Voulez-vous ajouter autre chose ?",
                    'context': 'initial',
                    'facture_data': {key: value for key, value in facture_data.items() if value is not None}
                }

                additions_to_ask[detected_type] = detected_value
                session['context'] = 'initial'
                return jsonify(response)
        else:
            answer = chatbot_logic(user_input, qa_data,"fr")
            print(answer)
            response = {
                    'response': answer,
                    'context': 'initial',
                    'facture_data': {key: value for key, value in facture_data.items() if value is not None}
                }
            session['context'] = 'initial'
            return jsonify(response)

    elif context == 'awaiting_confirmation':
        tag = closest_tag(user_input, qa_data, "fr")
        
        if tag == "oui":
            for item_type, item_value in pending_additions.items():
                id = ajouter_option(item_type, item_value)
                facture_data[item_type] = id
            response = {
                    'response': "Les informations suivantes ont été ajoutées avec succès : " + ', '.join([f"{k} : {v}" for k, v in pending_additions.items()]) + ". Voulez-vous ajouter autre chose ? si non taper confirmer",
                    'context': 'initial',
                    'facture_data': {key: value for key, value in facture_data.items() if value is not None},
                    'item_value': item_value,
                    'pending': pending_additions
                }
            session['context'] = 'initial'
            session['pending_additions'] = {}
            return jsonify(response)
        elif tag == "non":
            for item_type, item_value in pending_additions.items():
                facture_data[item_type]= {

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
                 'facture_data': {key: value for key, value in facture_data.items() if value is not None}
            }
            session['context'] = 'initial'
            session['pending_additions'] = {}
            return jsonify(response)
        else:
            response = {
                'response': "Je n'ai pas compris votre réponse. Voulez-vous ajouter les informations mentionnées ? Répondez par 'oui' ou 'non'.",
                'context': 'awaiting_confirmation',
                'pending_additions': pending_additions,
                'facture_data': {key: value for key, value in facture_data.items() if value is not None}
            }
            return jsonify(response)
    elif context== 'initial' and tag1 == "confirmer":
            add_facture(facture_data, api_url="https://pp-unum-back.etcinfo.tech/api/societe/factures", static_token="eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpYXQiOjE3MjA2MjU2NDcsImV4cCI6MTcyMDY2MTY0Nywicm9sZXMiOlsiUk9MRV9BRE1JTiJdLCJzY2hlbWFBY3RpdmUiOiJnZXN0aW9uX3ByZXByb2RfMTRfMDYiLCJjb21wYW55IjpbeyJub20iOiJFVEMiLCJjb2RlIjoiQ09MSSIsImFjdGl2ZSI6ZmFsc2V9LHsibm9tIjoiU09MQVZJVEUiLCJjb2RlIjoiU09MQSIsImFjdGl2ZSI6dHJ1ZX1dLCJub20iOiJhbGljZSIsInVzZXJuYW1lIjoiYWxpY2V2MkBldGNpbmZvLmZyIiwic29jaWV0ZSI6MX0.PMtxf0wsn1fgikUeLA4Cn21-fI4L_HvSKLtwdJYE4Pz7DnLckA--dPcZzcuWszlp-L33WE2POe--9TEDmZwe8oZA9nNDmEKlTA0Ek8B-NLW2j4pBkwkv3tm2PMeqS3YOGosFf8i7ypdXUvRiCbQ7FNJNZZ9cAOW-oTGENadaU_HRx3zj44JrBH89PAnghljJtgy2nEj18qf2zOMzrrSxYBN42EgbYlqlKwIxjPOqtpnXC48w_8qWx285i3sls-px2ZEcR4AtCrktaEl0zzb50F15YH-gfRdW40fxHS4eDTqidZu77_1rWu842R3XQLddad9RGdc_4_EsSYYjEFMuvg")
            
            response = {
                'response': f"facture ajouté avec succès." ,
                'context': 'initial',
                'facture_data': {key: value for key, value in facture_data.items() if value is not None}
            }
            session['context'] = 'initial'
            session['pending_additions'] = {}
            return jsonify(response)
       

    else:
        response = {
            'response': "Je n'ai pas compris votre demande. Pouvez-vous répéter ?",
            'context': 'initial'
        }
        session['context'] = 'initial'
        return jsonify(response)
  
 


if __name__ == '__main__':
    app.run(debug=True)