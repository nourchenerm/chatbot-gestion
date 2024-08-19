import json
import random
import spacy
from spacy.lang.fr.stop_words import STOP_WORDS as fr_stop_words
from spacy.lang.en.stop_words import STOP_WORDS as en_stop_words
from spacy.tokens import Doc
import re
import string
# Charger les questions et réponses depuis le fichier JSON
def load_qa(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        qa_data = json.load(file)
    return qa_data


nlp_fr = spacy.load('fr_core_news_md')
nlp_en = spacy.load('en_core_web_md')

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

# Trouver la question la plus proche
def get_closest_question(user_input, questions,language):
    best_similarity = 0.0
    closest_question = None

    user_input_processed = preprocess_text(user_input, language)

    for question in questions:
        question_processed = preprocess_text(question, language)
        if language == 'fr':
            similarity = nlp_fr(user_input_processed).similarity(nlp_fr(question_processed))
        elif language == 'en':
            similarity = nlp_en(user_input_processed).similarity(nlp_en(question_processed))
        else:
            continue  # Skip if language is unsupported
        
        if similarity > best_similarity:
            best_similarity = similarity
            closest_question = question
    
    return closest_question

# Fonction pour diviser le message en parties
def split_message(message):
    separators = r'[.,;!?&|]|\bet\b|\bou\b|\band\b|\bor\b'  # Séparateurs et mots-clés de séparation
    parts = re.split(separators, message)
    parts = [part.strip() for part in parts if part.strip()]
    return parts

# Fonction pour traiter chaque partie du message et générer une réponse
def chatbot_logic(user_input, qa_data, language):
    message = user_input.lower()

    # Diviser le message en parties
    parts = split_message(message)

    responses = []
    closest_tags = []

    for part in parts:
        # Réinitialiser les listes pour chaque partie du message
        questions = []
        question_answer_map = {}
        tags = []
 
        # Extraire les questions et réponses correspondantes des données QA
        for intent in qa_data["intents"]:
            if language in intent["patterns"]:
                for pattern in intent["patterns"][language]:
                    questions.append(pattern)
                    question_answer_map.setdefault(pattern, set()).update(intent["responses"][language])
                    tags.append(intent["tag"])  # Ajouter les tags correspondants

        # Trouver la question la plus proche pour cette partie
        closest_question = get_closest_question(part, questions, language)
        if closest_question:
            closest_tags.append(tags[questions.index(closest_question)])  # Ajouter le tag correspondant à la réponse
            
            response = random.choice(list(question_answer_map[closest_question]))  # Sélection aléatoire parmi les réponses uniques
            responses.append(response)
        else:
            if language == 'fr':
                responses.append("Désolé, je ne comprends pas cette question")
            elif language == 'en':
                responses.append("Sorry, I don't understand this question")
            else:
                responses.append("Sorry, I don't understand this question")
    
    # Concaténer toutes les réponses en une seule chaîne de caractères
    answer = ' '.join(responses)
    
    # Concaténer tous les tags correspondants en une seule chaîne de caractères    
    return answer


def closest_tag(user_input, qa_data, language):
    message = user_input.lower()

    # Diviser le message en parties
    parts = split_message(message)

    closest_tags = []

    for part in parts:
        # Réinitialiser les listes pour chaque partie du message
        questions = []
        question_answer_map = {}
        tags = []
 
        # Extraire les questions et réponses correspondantes des données QA
        for intent in qa_data["intents"]:
            if language in intent["patterns"]:
                for pattern in intent["patterns"][language]:
                    questions.append(pattern)
                    question_answer_map.setdefault(pattern, set()).update(intent["responses"][language])
                    tags.append(intent["tag"])  # Ajouter les tags correspondants

        # Trouver la question la plus proche pour cette partie
        closest_question = get_closest_question(part, questions, language)
        if closest_question:
            closest_tags.append(tags[questions.index(closest_question)])  # Ajouter le tag correspondant à la réponse

    
    return closest_tags[0]