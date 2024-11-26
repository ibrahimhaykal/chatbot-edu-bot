import streamlit as st
import random
import json
import re
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.preprocessing.text import tokenizer_from_json
from sklearn.preprocessing import LabelEncoder

# Load Model dan Tokenizer
model = load_model("chatbot_model.h5")

with open("tokenizer.json", "r") as tok_file:
    tokenizer_data = json.load(tok_file)
tokenizer = tokenizer_from_json(tokenizer_data)

with open("label_encoder.json", "r") as enc_file:
    encoder_classes = json.load(enc_file)
encoder = LabelEncoder()
encoder.classes_ = np.array(encoder_classes)

# Load Responses
with open("dataset.json", "r", encoding="utf-8") as file:
    data = json.load(file)
responses = {intent["tag"]: intent["responses"] for intent in data["intents"]}

# Preprocessing Function
def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    return text

# Prediction Function
def predict_intent(text):
    processed_text = preprocess_text(text)
    sequence = tokenizer.texts_to_sequences([processed_text])
    padded_sequence = pad_sequences(sequence, maxlen=model.input_shape[1], padding="post")
    
    # Prediksi intent
    prediction = model.predict(padded_sequence)
    intent_index = np.argmax(prediction)
    intent = encoder.classes_[intent_index]

    # Ambil respon sesuai intent
    if intent in responses:
        # Pilih secara acak dari daftar response
        response_data = random.choice(responses[intent])
        
        # Pastikan response_data adalah dictionary
        if isinstance(response_data, dict):
            response = response_data["bot"]
            user_follow_up = response_data.get("user_follow_up")
            bot_follow_up = response_data.get("bot_follow_up")
        else:
            # Jika response hanya string (fallback)
            response = response_data
            user_follow_up = None
            bot_follow_up = None
    else:
        response = "Maaf, saya belum memahami pertanyaan Anda. Bisa coba lagi?"
        user_follow_up = None
        bot_follow_up = None

    return intent, response, user_follow_up, bot_follow_up


# Streamlit UI
st.set_page_config(page_title="EduBot - ChatBot Edukasi", page_icon="📚")

st.title("🌟 EduBot Interaktif 🌟")
st.markdown("**Halo! Saya EduBot, asisten Anda untuk belajar. Mari kita mulai!** 💬")

# Initialize chat session
if "messages" not in st.session_state:
    # Bot starts conversation using 'welcome' tag
    welcome_message = random.choice(responses.get("welcome", ["Halo! Selamat datang di EduBot! Apa yang ingin Anda pelajari hari ini?"]))
    st.session_state.messages = [{"role": "assistant", "content": welcome_message}]
if "follow_up" not in st.session_state:
    st.session_state.follow_up = None  # Simpan bot_follow_up jika ada

st.markdown("---")

# Display chat history
for message in st.session_state.messages:
    if message["role"] == "user":
        with st.chat_message("user"):
            st.markdown(f"👤 **You**: {message['content']}")
    else:
        with st.chat_message("assistant"):
            st.markdown(f"🤖 **Bot**: {message['content']}")

# Input user message
prompt = st.chat_input("💬 Ketik pesan Anda di sini...")

if prompt:
    # Preprocess user input
    processed_text = preprocess_text(prompt)

    # Predict intent and generate response
    intent, response, user_follow_up, bot_follow_up = predict_intent(prompt)

    # Append user message
    with st.chat_message("user"):
        st.markdown(f"👤 **You**: {prompt}")
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Tindak lanjut: periksa apakah user_follow_up terpenuhi
    if st.session_state.follow_up and prompt.lower() == st.session_state.follow_up["user_follow_up"].lower():
        response = st.session_state.follow_up["bot_follow_up"]
        st.session_state.follow_up = None  # Hapus tindak lanjut setelah ditampilkan
    else:
        # Simpan bot_follow_up untuk percakapan berikutnya
        if bot_follow_up:
            st.session_state.follow_up = {"user_follow_up": user_follow_up, "bot_follow_up": bot_follow_up}

    # Append bot response
    with st.chat_message("assistant"):
        st.markdown(f"🤖 **Bot**: {response}")
    st.session_state.messages.append({"role": "assistant", "content": response})

# Footer
st.markdown("---")
st.markdown("<center><small>💡 EduBot © 2024 - Platform Edukasi untuk Masa Depan</small></center>", unsafe_allow_html=True)
