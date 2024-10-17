import yaml
import streamlit as st
import streamlit_authenticator as stauth
from yaml.loader import SafeLoader
from streamlit_authenticator.utilities import (CredentialsError,
                                               ForgotError,
                                               Hasher,
                                               LoginError,
                                               RegisterError,
                                               ResetError,
                                               UpdateError)
from utils import make_certificates
from streamlit_option_menu import option_menu


# Sahifa sozlamalari
st.set_page_config(page_title="JBNUU Conferences", page_icon="🔖", layout="wide", initial_sidebar_state="expanded")

with open('src/style.css','r', encoding='utf-8') as style:
    st.markdown(f"<style>{style.read()}</style>", unsafe_allow_html=True)
    
st.title("💡 Konferensiya ishtirokchilari uchun sertifikat tayyorlash sahifasi")
st.caption("Mirzo Ulugʻbek nomidagi Oʻzbekiston Milliy universitetining Jizzax filialida oʻtkaziladigan xalqaro ilmiy-texnik anjumani")

# Yon panel
with st.sidebar:
    selected = option_menu("Bosh sahifa", ["Sertifikat olish", 'Maqola talablari', "Dasturchi haqida"], icons=['house', 'gear', 'list-task'], menu_icon="cast", default_index=0)
    st.write("Konferensiya materiali")
    st.image("src/To'plam yuzi_1.jpg", width=150, caption="Konferensiya xati", clamp=True)
    st.link_button("Anjuman xati", use_container_width=True, url="src/Xalqaro konferensiya_O'zMU JF_Axborot xati.pdf")

if selected == "Sertifikat olish":
    # YAML konfiguratsiyani yuklash
    with open('src/config.yaml', 'r', encoding='utf-8') as file:
        config = yaml.load(file, Loader=SafeLoader)

    # Parollarni hash qilish
    stauth.Hasher.hash_passwords(config['credentials'])

    # Autentifikatsiya yaratish
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )

    # Login funksiya
    def login():
        try:
            authenticator.login(location='main', clear_on_submit=True)
            if st.session_state['authentication_status']:
                authenticator.logout("Chiqish")
                st.success(f"Assalomu alaykum {st.session_state['name']}, o'zingizning barcha ma'lumotlaringizni kiriting")
                # Sertifikat uchun forma
                fish = st.text_input("Familiya ism, sharifingizni kiriting", placeholder="Ulug'murodov Shoh Abbos Baxodir o'g'li", max_chars=200)
                maqola_matni = st.text_input("Maqolangiz mavzusini kiriting", placeholder="Brayl matnida yozilgan ma'lumotlarning ishonchliligini oshirish algoritmlari", max_chars=200)
                
                shuba = st.radio("O'z sho'bangizni kiriting", 
                                options=[
                                    "1️⃣-sho‘ba. Sun’iy intellekt va axborot xavfsizligi",
                                    "2️⃣-sho‘ba. Raqamli iqtisodiyot va raqamli transformatsiya",
                                    "3️⃣-sho‘ba. Ta’lim texnologiyalari va barqaror rivojlanish",
                                    "4️⃣-sho‘ba. Biotexnologiya sohasida innovatsion tadqiqotlar",
                                    "5️⃣-sho‘ba. Psixologiya va pedagogikada zamonaviy metodlar va texnologiyalar",
                                    "6️⃣-sho‘ba. Global transformatsiyalar sharoitida ijtimoiy tadqiqotlar va zamonaviy filologiyaning dolzarb muammolari"
                                ])
                
                createButton = st.button("Sertifikat yaratish", use_container_width=True, type='primary', icon='✅')
                
                forgot_username()
                if createButton and fish and maqola_matni:
                    rasm = st.image(make_certificates(fish, maqola_matni), caption=shuba)
                else:
                    st.warning("Ma'lumotlarni to'liq to'ldiring.")
                    
            elif st.session_state['authentication_status'] is False:
                st.error('Login yoki parol noto\'g\'ri.')
                register()
                authenticator.experimental_guest_login('Login with Google', provider='google',oauth2=config['oauth2'])
                forgot_password()
            elif st.session_state['authentication_status'] is None:
                register()
                st.warning('Iltimos, foydalanuvchi nomi va parolingizni kiriting.')

        except Exception as e:
            st.error(f"Xatolik kodi: {e}")

    # Ro'yxatdan o'tish
    def register():
        register_button = st.button("Ro'yxatdan o'tish", type='primary', icon='🎁')
        if register_button:
            try:
                email, username, name = authenticator.register_user(captcha=True, location='sidebar', roles='viewer')
                if email:
                    st.success(f"Foydalanuvchi {username}, {name} bilan muvaffaqiyatli ro'yxatdan o'tdi.")
                    update_config_file()
                    update_user_details()
                else:
                    st.warning("Ro'yxatdan o'tishda xatolik yuz berdi.")
            except Exception as e:
                st.error(f"Xatolik kodi: {e}")
                
    # Reset password
    def reset_password():
        reset_button = st.button("Parolni yangilash", type='primary', icon='🎁')
        if st.session_state['authentication_status'] and reset_button:
            try:
                if authenticator.reset_password(st.session_state['username']):
                    st.success('Password modified successfully')
                update_config_file()
            except Exception as e:
                st.error(e)

    # Parolni tiklash
    def forgot_password():
        forgetBtn = st.button("Foydalanuvchi parolini tiklash", icon='🔴')
        if forgetBtn:
            # Creating a forgot password widget
            try:
                (username_of_forgotten_password, email_of_forgotten_password,new_random_password) = authenticator.forgot_password()
                if username_of_forgotten_password:
                    st.success(f"New password **'{new_random_password}'** to be sent to user securely")
                    config['credentials']['usernames'][username_of_forgotten_password]['pp'] = new_random_password
                    # Random password to be transferred to the user securely
                elif not username_of_forgotten_password:
                    st.error('Foydalanuvchi topilmadi')
            except ForgotError as e:
                st.error(e)
        update_config_file()

    # Foydalanuvchi nomini tiklash
    def forgot_username():
        forgetBtn = st.button("Foydalanuvchi nomini tiklash", type='primary', icon='🧑')
        if forgetBtn:
            # Creating a forgot username widget
            try:
                (username_of_forgotten_username,
                email_of_forgotten_username) = authenticator.forgot_username()
                if username_of_forgotten_username:
                    st.success(f"Username **'{username_of_forgotten_username}'** to be sent to user securely")
                    update_user_details()
                    update_config_file()
                    # Username to be transferred to the user securely
                elif not username_of_forgotten_username:
                    st.error('Email not found')
            except ForgotError as e:
                st.error(e)

    # Foydalanuvchi ma'lumotlarini yangilash
    def update_user_details():
            # Creating an update user details widget
        if st.session_state["authentication_status"]:
            try:
                if authenticator.update_user_details(st.session_state["username"]):
                    st.success('Entries updated successfully')
            except UpdateError as e:
                st.error(e)

    # YAML faylini yangilash
    def update_config_file():
        with open('src/config.yaml', 'w', encoding='utf-8') as file:
            yaml.dump(config, file, default_flow_style=False)

    # Asosiy qism
    if __name__ == "__main__":
        login()

elif selected=="Maqola talablari":
    st.write("*Axborot xati*")
    st.image("src/settingJPG/Xalqaro konferensiya_O'zMU JF_Axborot xati (2)_1.jpg")
    st.image("src/settingJPG/Xalqaro konferensiya_O'zMU JF_Axborot xati (2)_2.jpg")
    st.image("src/settingJPG/Xalqaro konferensiya_O'zMU JF_Axborot xati (2)_3.jpg")
    st.image("src/settingJPG/Xalqaro konferensiya_O'zMU JF_Axborot xati (2)_4.jpg")
    st.link_button("1-2-3-shoʻbalarga telegram havola", url=" https://t.me/UzMU_JF_conf_1_2_3_shob", icon="1️⃣")
    st.link_button("4-5-6-shoʻbalarga telegram havola", url=" https://t.me/Uzmu_JF_konf_4_5_6_shuba", icon="2️⃣")

elif selected == "Dasturchi haqida":
    st.write("*Dasturchi haqida*")
    st.markdown("<div class='circle-container'><img id='circleImage' src='https://avatars.githubusercontent.com/u/71746304?s=400&u=12a8397519c5065d6af00235fb2ac9b1d2e9965b&v=4' alt='Rasm'> </div><br/> <div id='badges' align='center'> <a href='https://t.me/shohabbosdev'> <img src='https://img.shields.io/badge/telegram-blue?logo=telegram&logoColor=white' alt='Bu telegram badges'> </a> <a href='https://youtube.com/@shohabbosdev'> <img src='https://img.shields.io/badge/youtube-white?logo=youtube&logoColor=red' alt='Bu youtube badges'> </a> <a href='https://instagram.com/shohabbosdev'>  <img src='https://img.shields.io/badge/instagram-red?logo=instagram&logoColor=white' alt='Bu instagram badges'></a> <a href='https://facebook.com/shohabbosdev'>  <img src='https://img.shields.io/badge/facebook-white?logo=facebook&logoColor=blue' alt='Bu facebook badges'> </a><a href='https://x.com/shohabbosdev'> <img src='https://img.shields.io/badge/twitter-black?logo=x&logoColor=white' alt='Bu twitter badges'/>  </a><br>  <img src='https://komarev.com/ghpvc/?username=freedom-1&label=PROFILNI+KORISHLAR+SONI' alt=''/> </div>",unsafe_allow_html=True)