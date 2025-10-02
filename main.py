import yaml
import json
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
from utils import make_certificates, create_pdf_certificate, get_available_templates
from streamlit_option_menu import option_menu
import plotly.express as px
import pandas as pd
import os
from PIL import Image
import shutil

# JSON faylni o'qib olish
with open('src/azolar.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Konfiguratsiya faylini o'qib olish
with open('src/config.yaml', 'r', encoding='utf-8') as file:
    config = yaml.load(file, Loader=SafeLoader)
    
# Sahifa sozlamalari
st.set_page_config(page_title="JBNUU Conferences", page_icon="🔖", layout="wide", initial_sidebar_state="expanded")

# Urinishlar sonini kuzatish uchun session state ni ishga tushiramiz
if 'login_attempts' not in st.session_state:
    st.session_state.login_attempts = {}

# Maksimal urinishlar soni
MAX_LOGIN_ATTEMPTS = 3

with open('src/style.css','r', encoding='utf-8') as style:
    st.markdown(f"<style>{style.read()}</style>", unsafe_allow_html=True)
    
st.markdown("# 💡 :rainbow[Konferensiya ishtirokchilari uchun sertifikat tayyorlash sahifasi]")
st.caption("Mirzo Ulugʻbek nomidagi Oʻzbekiston Milliy universitetining Jizzax filialida oʻtkaziladigan xalqaro ilmiy-texnik anjumani")

# Foydalanuvchi rolini tekshirish funksiyasi
def check_role(required_roles):
    """Foydalanuvchi rolini tekshirish"""
    if st.session_state.get('authentication_status'):
        username = st.session_state.get('username')
        user_roles = config['credentials']['usernames'].get(username, {}).get('roles', [])
        return any(role in user_roles for role in required_roles)
    return False

# YAML faylini yangilash
def update_config_file(config):
    with open('src/config.yaml', 'w', encoding='utf-8') as file:
        yaml.dump(config, file, default_flow_style=False)

# JSON faylini yangilash
def update_json_file(data):
    with open('src/azolar.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

# Parollarni hash qilish
def hash_password(password):
    # Yangi Hasher obyektini yaratish va parolni hash qilish
    return Hasher.hash(password)

# Yon panel
with st.sidebar:
    # Asosiy menyuni yaratish
    menu_items = ["Sertifikat olish"]
    menu_icons = ['house']
    
    # Agar foydalanuvchi tizimga kirgan bo'lsa
    if st.session_state.get('authentication_status'):
        # Foydalanuvchi rolini tekshirish
        user_roles = []
        username = st.session_state.get('username')
        user_roles = config['credentials']['usernames'].get(username, {}).get('roles', [])
        
        # Agar foydalanuvchi admin bo'lsa, sertifikat shablonini boshqarish menyusini qo'shamiz
        if check_role(['admin']):
            menu_items.append("Sertifikat shablonini boshqarish")
            menu_icons.append('image')
        
        # Agar foydalanuvchi admin, editor yoki viewer bo'lsa, statistika menyusini qo'shamiz
        if check_role(['admin', 'editor', 'viewer']):
            menu_items.append("Statistika")
            menu_icons.append('bar-chart')
        
        # Agar foydalanuvchi admin yoki editor bo'lsa, foydalanuvchilar menyusini qo'shamiz
        if check_role(['admin', 'editor']):
            menu_items.append("Foydalanuvchilar")
            menu_icons.append('people')
    
    menu_items.append("Dasturchi haqida")
    menu_icons.append('list-task')
    
    selected = option_menu("Bosh sahifa", menu_items, 
                          icons=menu_icons, 
                          menu_icon="cast", default_index=0)

if selected == "Sertifikat olish":
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
            # Foydalanuvchi IP manzilini olish (Streamlit-da session ID dan foydalanamiz)
            user_identifier = st.session_state.get('username', 'unknown_user')
            
            # Agar foydalanuvchi uchun urinishlar soni mavjud bo'lmasa, uni yaratamiz
            if user_identifier not in st.session_state.login_attempts:
                st.session_state.login_attempts[user_identifier] = 0
            
            # Agar maksimal urinishlar sonidan oshib ketgan bo'lsa, kirishni bloklaymiz
            if st.session_state.login_attempts[user_identifier] >= MAX_LOGIN_ATTEMPTS:
                st.error(f"Siz maksimal urinishlar sonini ({MAX_LOGIN_ATTEMPTS}) oshib ketdingiz. Kirish vaqtincha bloklangan.")
                # "Himoyani tozalash" tugmasini ko'rsatamiz (faqat development muhitida)
                if st.button("🔒 Himoyani tozalash"):
                    st.session_state.login_attempts[user_identifier] = 0
                    st.success("Himoya tozalandi. Endi qayta urinib ko'rishingiz mumkin.")
                    st.rerun()
                return
            
            authenticator.login(location='main', clear_on_submit=True)
            if st.session_state['authentication_status']:
                # Muvaffaqiyatli login bo'lganda urinishlar sonini qayta tiklaymiz
                st.session_state.login_attempts[user_identifier] = 0
                authenticator.logout("Chiqish")
                st.success(f"Assalomu alaykum {st.session_state['name']}, o'zingizning barcha ma'lumotlaringizni kiriting")
                # Sertifikat uchun forma
                # fish = st.text_input("Familiya ism, sharifingizni kiriting", placeholder="Ulug'murodov Shoh Abbos Baxodir o'g'li", max_chars=200)
                # 1. Shuba tanlash
                shuba = st.selectbox("Shubani tanlang:", list(data.keys()))
                
                # Standart shablonni olish
                selected_template = config.get('settings', {}).get('default_template', 'template_1.png')
                
                # Agar admin foydalanuvchi bo'lsa, shablonni ko'rsatish (tanlash imkonini bermasdan)
                if check_role(['admin']):
                    st.info(f"Standart sertifikat shabloni: {selected_template}")
                
                # Initsializatsiya
                familiya = None
                maqola_matni = None
                
                # 2. Familiya tanlash (agar shuba tanlangan bo'lsa)
                if shuba:
                    familiyalar = list(data[shuba].keys())  # tanlangan shubaga mos familiyalar
                    familiya = st.selectbox("Familiyani tanlang:", familiyalar)

                    # 3. Mavzuni ko'rsatish (agar familiya tanlangan bo'lsa)
                    if familiya:
                        mavzu = data[shuba][familiya]
                        maqola_matni = st.text_input("Maqolangiz mavzusini kiriting", value=mavzu,placeholder="Brayl matnida yozilgan ma'lumotlarning ishonchliligini oshirish algoritmlari", disabled=True)
                        # st.write(f"Tanlangan familiyaga mos mavzu: **{mavzu}**")
                
                createButton = st.button("Sertifikat yaratish", use_container_width=True, type='primary', icon='✅')
                
                # Global o'zgaruvchilar
                if 'certificate_image' not in st.session_state:
                    st.session_state.certificate_image = None
                if 'shuba_name' not in st.session_state:
                    st.session_state.shuba_name = None
                
                if createButton and familiya and maqola_matni:
                    st.session_state.certificate_image = make_certificates(familiya, maqola_matni, selected_template)
                    st.session_state.shuba_name = shuba
                    st.image(st.session_state.certificate_image, caption=shuba, use_container_width=True)
                    
                    # PDF yuklab olish tugmasi
                    pdf_buffer = create_pdf_certificate(familiya, maqola_matni, selected_template)
                    st.download_button(
                        label="PDF sertifikatni yuklab olish",
                        data=pdf_buffer,
                        file_name=f"sertifikat_{familiya}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                elif createButton:
                    st.warning("Ma'lumotlarni to'liq to'ldiring.")
                    
            elif st.session_state['authentication_status'] is False:
                # Login yoki parol noto'g'ri bo'lsa, urinishlar sonini oshiramiz
                st.session_state.login_attempts[user_identifier] += 1
                remaining_attempts = MAX_LOGIN_ATTEMPTS - st.session_state.login_attempts[user_identifier]
                if remaining_attempts > 0:
                    st.error(f'Login yoki parol noto\'g\'ri. Sizda {remaining_attempts} ta urinish qoldi.')
                else:
                    st.error(f"Siz maksimal urinishlar sonini ({MAX_LOGIN_ATTEMPTS}) oshib ketdingiz. Kirish vaqtincha bloklangan.")
                
                authenticator.experimental_guest_login('Login with Google', provider='google',oauth2=config['oauth2'])
            elif st.session_state['authentication_status'] is None:
                
                st.warning('Iltimos, foydalanuvchi nomi va parolingizni kiriting.')

        except Exception as e:
            st.error(f"Xatolik kodi: {e}")

    # Ro'yxatdan o'tish
    def register():
        register_button = st.button("Ro'yxatdan o'tish", type='primary', icon='🎁')
        if register_button:
            try:
                email, username, name = authenticator.register_user(captcha=True, location='sidebar', roles=['viewer'])
                if email:
                    st.success(f"Foydalanuvchi {username}, {name} bilan muvaffaqiyatli ro'yxatdan o'tdi.")
                    update_config_file(config)
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
                update_config_file(config)
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
        update_config_file(config)

    # Foydalanuvchi ma'lumotlarini yangilash
    def update_user_details():
            # Creating an update user details widget
        if st.session_state["authentication_status"]:
            try:
                if authenticator.update_user_details(st.session_state["username"]):
                    st.success('Entries updated successfully')
            except UpdateError as e:
                st.error(e)

    # Asosiy qism
    if __name__ == "__main__":
        login()

elif selected == "Sertifikat shablonini boshqarish":
    st.markdown("# 🖼️ Sertifikat shablonini boshqarish")
    
    # Faqat admin foydalanuvchilar kirishi mumkin
    if not check_role(['admin']):
        st.error("Sizda bu sahifaga kirish huquqi mavjud emas!")
        st.stop()
    
    # Joriy standart shablonni ko'rsatish
    default_template = config.get('settings', {}).get('default_template', 'template_1.png')
    st.markdown(f"## 📋 Joriy standart sertifikat shabloni: {default_template}")
    
    # Mavjud shablonlarni olish
    available_templates = get_available_templates()
    
    # Joriy sertifikat shablonlarini ko'rsatish
    st.markdown("## 📋 Mavjud sertifikat shablonlari")
    if available_templates:
        cols = st.columns(min(3, len(available_templates)))  # 3 ta ustun
        for i, template in enumerate(available_templates):
            with cols[i % 3]:
                template_path = os.path.join('src', 'templates', template)
                st.image(template_path, caption=template, use_container_width=True)
                # Agar bu shablon standart bo'lsa, maxsus belgi ko'rsatamiz
                if template == default_template:
                    st.markdown("⭐ **Standart**")
                else:
                    # Agar bu shablon standart bo'lmasa, uni standart qilib belgilash tugmasini ko'rsatamiz
                    if st.button(f"Standart qilib belgilash", key=f"set_default_{template}"):
                        # Konfiguratsiya faylini yangilash
                        config['settings']['default_template'] = template
                        update_config_file(config)
                        st.success(f"'{template}' endi standart sertifikat shabloni!")
                        st.rerun()
                
                # O'chirish tugmasi uchun session state dan foydalanamiz
                if st.button(f"❌ O'chirish", key=f"delete_{template}"):
                    template_path = os.path.join('src', 'templates', template)
                    if os.path.exists(template_path):
                        os.remove(template_path)
                        st.success(f"{template} o'chirildi!")
                        st.rerun()
    else:
        st.warning("Hozirda sertifikat shablonlari mavjud emas")
    
    # Yangi sertifikat shablonini yuklash
    st.markdown("## 📤 Yangi sertifikat shablonini yuklash")
    st.info("Eslatma: Yangi sertifikat shabloni PNG formatida bo'lishi kerak")
    
    uploaded_file = st.file_uploader("PNG faylni tanlang", type=['png'], key="template_uploader")
    
    if uploaded_file is not None:
        # Yangi fayl nomini aniqlash
        template_name = uploaded_file.name
        template_path = os.path.join('src', 'templates', template_name)
        
        # Agar fayl nomi mavjud bo'lsa, uni yangilash
        if os.path.exists(template_path):
            base_name, ext = os.path.splitext(template_name)
            counter = 1
            while os.path.exists(os.path.join('src', 'templates', f"{base_name}_{counter}{ext}")):
                counter += 1
            template_name = f"{base_name}_{counter}{ext}"
            template_path = os.path.join('src', 'templates', template_name)
        
        # Yangi faylni saqlash
        with open(template_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        
        # Rasm hajmini tekshirish
        try:
            img = Image.open(template_path)
            st.success(f"Rasm hajmi: {img.size[0]}x{img.size[1]} pixels")
            st.success(f"Yangi sertifikat shabloni '{template_name}' muvaffaqiyatli yuklandi!")
            st.info("Shablonlar ro'yxatini yangilash uchun sahifani qayta yuklang")
        except Exception as e:
            st.error(f"Faylni ochishda xatolik: {e}")
            # Xato faylni o'chirib tashlash
            if os.path.exists(template_path):
                os.remove(template_path)
    
    # Backup shablonni qayta tiklash
    st.markdown("## 🔄 Backup shablonni qayta tiklash")
    if os.path.exists('src/Sertifikat_backup.png'):
        st.info("Backup sertifikat shabloni mavjud")
        if st.button("Backup shablonni qayta tiklash"):
            shutil.copy('src/Sertifikat_backup.png', 'src/Sertifikat.png')
            st.success("Backup shablon muvaffaqiyatli qayta tiklandi!")
            st.rerun()
    else:
        st.info("Hozirda backup sertifikat shabloni mavjud emas")

elif selected == "Statistika":
    # Faqat tizimga kirgan foydalanuvchilar kirishi mumkin
    if not st.session_state.get('authentication_status'):
        st.error("Sizda bu sahifaga kirish huquqi mavjud emas! Iltimos, tizimga kiring.")
        st.stop()
    
    # Faqat admin, editor yoki viewer rollariga ega foydalanuvchilar kirishi mumkin
    if not check_role(['admin', 'editor', 'viewer']):
        st.error("Sizda bu sahifaga kirish huquqi mavjud emas!")
        st.stop()
    
    st.markdown("# 📊 Statistika")
    
    # Statistik ma'lumotlarni tayyorlash
    stats_data = []
    total_participants = 0
    
    for shuba, participants in data.items():
        count = len(participants)
        stats_data.append({"Shuba": shuba, "Ishtirokchilar soni": count})
        total_participants += count
    
    st.markdown(f"**Jami ishtirokchilar soni:** {total_participants}")
    
    # DataFrame yaratish
    df = pd.DataFrame(stats_data)
    
    # Bar chart chizish
    fig = px.bar(df, x="Shuba", y="Ishtirokchilar soni", 
                 title="Har bir shubada ishtirokchilar soni",
                 color="Ishtirokchilar soni",
                 color_continuous_scale="viridis")
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)
    
    # Jadval ko'rinishida
    st.markdown("### 📋 Batafsil statistika")
    st.dataframe(df, use_container_width=True)

elif selected == "Foydalanuvchilar":
    # Faqat tizimga kirgan foydalanuvchilar kirishi mumkin
    if not st.session_state.get('authentication_status'):
        st.error("Sizda bu sahifaga kirish huquqi mavjud emas! Iltimos, tizimga kiring.")
        st.stop()
    
    # Faqat admin va editor rollariga ega foydalanuvchilar kirishi mumkin
    if not check_role(['admin', 'editor']):
        st.error("Sizda bu sahifaga kirish huquqi mavjud emas!")
        st.stop()
    
    st.markdown("# 👥 Foydalanuvchilar")
    
    # Tablarni yaratish
    tab_names = []
    
    # Agar foydalanuvchi admin bo'lsa, foydalanuvchilarni boshqarish tabini qo'shamiz
    if check_role(['admin']):
        tab_names.append("Foydalanuvchi boshqarish")
    
    # Agar foydalanuvchi admin yoki editor bo'lsa, azolar ma'lumotlarini tahrirlash tabini qo'shamiz
    if check_role(['admin', 'editor']):
        tab_names.append("Azolar ma'lumotlarini tahrirlash")
    
    # Qidiruv tabini faqat admin foydalanuvchilarga ko'rsatamiz
    if check_role(['admin']):
        tab_names.append("Qidiruv")
    
    # Tablarni yaratish
    tabs = st.tabs(tab_names)
    
    # Tab indekslarini aniqlash
    user_management_tab_index = 0 if check_role(['admin']) else -1
    azolar_edit_tab_index = 1 if check_role(['admin']) else 0
    search_tab_index = len(tab_names) - 1 if check_role(['admin']) else -1
    
    # Foydalanuvchilarni yuklash
    users = config['credentials']['usernames']
    
    # Foydalanuvchi boshqarish tabi (faqat admin uchun)
    if check_role(['admin']) and user_management_tab_index >= 0:
        with tabs[user_management_tab_index]:
            st.markdown("## 🛠️ Foydalanuvchi boshqarish")
            
            # Yangi foydalanuvchi qo'shish
            with st.expander("➕ Yangi foydalanuvchi qo'shish"):
                new_username = st.text_input("Foydalanuvchi nomi")
                new_email = st.text_input("Email")
                new_first_name = st.text_input("Ism")
                new_last_name = st.text_input("Familiya")
                new_password = st.text_input("Parol", type="password")
                new_roles = st.multiselect("Rollar", ["admin", "editor", "viewer"], default=["viewer"], key="new_user_roles")
                
                if st.button("Foydalanuvchi qo'shish"):
                    if new_username and new_email and new_first_name and new_last_name and new_password:
                        # Foydalanuvchi mavjudligini tekshirish
                        if new_username not in users:
                            # Yangi foydalanuvchini qo'shish
                            users[new_username] = {
                                "email": new_email,
                                "first_name": new_first_name,
                                "last_name": new_last_name,
                                "password": hash_password(new_password),
                                "roles": new_roles
                            }
                            
                            # Konfiguratsiya faylini yangilash
                            update_config_file(config)
                            st.success(f"{new_username} foydalanuvchisi muvaffaqiyatli qo'shildi!")
                            st.rerun()
                        else:
                            st.error("Bu foydalanuvchi nomi allaqachon mavjud!")
                    else:
                        st.error("Barcha maydonlarni to'ldiring!")
            
            # Foydalanuvchini tahrirlash
            st.markdown("## ✏️ Foydalanuvchini tahrirlash")
            edit_username = st.selectbox("Tahrirlash uchun foydalanuvchini tanlang", list(users.keys()))
            
            if edit_username:
                user_data = users[edit_username]
                edit_email = st.text_input("Email", value=user_data.get("email", ""))
                edit_first_name = st.text_input("Ism", value=user_data.get("first_name", ""))
                edit_last_name = st.text_input("Familiya", value=user_data.get("last_name", ""))
                edit_roles = st.multiselect("Rollar", ["admin", "editor", "viewer"], 
                                        default=user_data.get("roles", ["viewer"]), 
                                        key=f"edit_user_roles_{edit_username}")
                
                # Parolni o'zgartirish
                change_password = st.checkbox("Parolni o'zgartirish")
                new_password = ""
                if change_password:
                    new_password = st.text_input("Yangi parol", type="password", key=f"new_password_{edit_username}")
                
                if st.button("Foydalanuvchini yangilash"):
                    # Foydalanuvchi ma'lumotlarini yangilash
                    users[edit_username]["email"] = edit_email
                    users[edit_username]["first_name"] = edit_first_name
                    users[edit_username]["last_name"] = edit_last_name
                    users[edit_username]["roles"] = edit_roles
                    
                    # Agar parol o'zgartirilmoqda bo'lsa
                    if change_password and new_password:
                        users[edit_username]["password"] = hash_password(new_password)
                    
                    # Konfiguratsiya faylini yangilash
                    update_config_file(config)
                    st.success(f"{edit_username} foydalanuvchisi muvaffaqiyatli yangilandi!")
                    st.rerun()
                
                # Foydalanuvchini o'chirish
                if st.button("Foydalanuvchini o'chirish", type="primary"):
                    if edit_username in users:
                        del users[edit_username]
                        # Konfiguratsiya faylini yangilash
                        update_config_file(config)
                        st.success(f"{edit_username} foydalanuvchisi muvaffaqiyatli o'chirildi!")
                        st.rerun()
    
    # Azolar ma'lumotlarini tahrirlash tabi (admin va editor uchun)
    if check_role(['admin', 'editor']) and azolar_edit_tab_index >= 0:
        with tabs[azolar_edit_tab_index]:
            st.markdown("## 📝 Azolar ma'lumotlarini tahrirlash")
            
            # Shubalarni ro'yxat qilish
            shubalar = list(data.keys())
            selected_shuba = st.selectbox("Shubani tanlang", shubalar)
            
            if selected_shuba:
                # Tanlangan shubadagi ishtirokchilarni ko'rsatish
                st.markdown(f"### {selected_shuba} ishtirokchilari")
                
                # Yangi qatnashchini qo'shish
                with st.expander("➕ Yangi qatnashchi qo'shish"):
                    new_fio = st.text_input("Familiya Ism Sharif")
                    new_mavzu = st.text_input("Mavzu")
                    
                    if st.button("Qatnashchini qo'shish"):
                        if new_fio and new_mavzu:
                            # Yangi qatnashchini qo'shish
                            data[selected_shuba][new_fio] = new_mavzu
                            # JSON faylini yangilash
                            update_json_file(data)
                            st.success(f"{new_fio} qatnashchisi muvaffaqiyatli qo'shildi!")
                            st.rerun()
                        else:
                            st.error("Barcha maydonlarni to'ldiring!")
                
                # Mavjud qatnashchilarni tahrirlash
                st.markdown("### Mavjud qatnashchilarni tahrirlash")
                participants = data[selected_shuba]
                
                # Har bir qatnashchi uchun tahrirlash imkoniyati
                for fio, mavzu in participants.items():
                    with st.expander(f"📝 {fio}"):
                        edited_fio = st.text_input("Familiya Ism Sharif", value=fio, key=f"fio_{fio}")
                        edited_mavzu = st.text_input("Mavzu", value=mavzu, key=f"mavzu_{fio}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Yangilash", key=f"update_{fio}"):
                                # Agar FIO o'zgartirilgan bo'lsa, eski yozuvni o'chirib tashlaymiz
                                if edited_fio != fio:
                                    del data[selected_shuba][fio]
                                
                                # Yangi yoki o'zgartirilgan yozuvni qo'shamiz
                                data[selected_shuba][edited_fio] = edited_mavzu
                                
                                # JSON faylini yangilash
                                update_json_file(data)
                                st.success(f"{edited_fio} ma'lumotlari yangilandi!")
                                st.rerun()
                        
                        with col2:
                            if st.button("O'chirish", key=f"delete_{fio}"):
                                # Qatnashchini o'chirish
                                del data[selected_shuba][fio]
                                # JSON faylini yangilash
                                update_json_file(data)
                                st.success(f"{fio} o'chirildi!")
                                st.rerun()
    
    # Qidiruv tabi (faqat admin uchun)
    if check_role(['admin']) and search_tab_index >= 0:
        with tabs[search_tab_index]:
            # Foydalanuvchilarni qidirish
            st.markdown("## 🔍 Foydalanuvchilarni qidirish")
            
            # Qidiruv maydoni
            search_query = st.text_input("Qidiruv", placeholder="Foydalanuvchi nomi, ismi yoki emailni kiriting...")
            
            # Filtirlangan foydalanuvchilar
            filtered_users = {}
            if search_query:
                for username, user_data in users.items():
                    # Qidiruv so'rovi foydalanuvchi nomi, ismi yoki emailda mavjud bo'lsa
                    if (search_query.lower() in username.lower() or 
                        search_query.lower() in user_data.get('first_name', '').lower() or
                        search_query.lower() in user_data.get('last_name', '').lower() or
                        search_query.lower() in user_data.get('email', '').lower()):
                        filtered_users[username] = user_data
            else:
                filtered_users = users
            
            # Foydalanuvchilar jadvali
            if filtered_users:
                st.markdown(f"### 📋 Topilgan foydalanuvchilar ({len(filtered_users)})")
                
                # Foydalanuvchilar uchun DataFrame yaratish
                user_data = []
                for username, user_info in filtered_users.items():
                    user_data.append({
                        "Foydalanuvchi nomi": username,
                        "Ism": user_info.get('first_name', ''),
                        "Familiya": user_info.get('last_name', ''),
                        "Email": user_info.get('email', ''),
                        "Ro'lar": ', '.join(user_info.get('roles', [])) if user_info.get('roles') else ''
                    })
                
                df = pd.DataFrame(user_data)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("Hech qanday foydalanuvchi topilmadi.")

elif selected == "Dasturchi haqida":
    st.write("*Dasturchi haqida*")
    st.markdown("<div class='circle-container'><img id='circleImage' src='https://avatars.githubusercontent.com/u/71746304?s=400&u=12a8397519c5065d6af00235fb2ac9b1d2e9965b&v=4' alt='Rasm'> </div><br/> <div id='badges' align='center'> <a href='https://t.me/shohabbosdev'> <img src='https://img.shields.io/badge/telegram-blue?logo=telegram&logoColor=white' alt='Bu telegram badges'> </a> <a href='https://youtube.com/@shohabbosdev'> <img src='https://img.shields.io/badge/youtube-white?logo=youtube&logoColor=red' alt='Bu youtube badges'> </a> <a href='https://instagram.com/shohabbosdev'>  <img src='https://img.shields.io/badge/instagram-red?logo=instagram&logoColor=white' alt='Bu instagram badges'></a> <a href='https://facebook.com/shohabbosdev'>  <img src='https://img.shields.io/badge/facebook-white?logo=facebook&logoColor=blue' alt='Bu facebook badges'> </a><a href='https://x.com/shohabbosdev'> <img src='https://img.shields.io/badge/twitter-black?logo=x&logoColor=white' alt='Bu twitter badges'/>  </a><br>  <img src='https://komarev.com/ghpvc/?username=freedom-1&label=PROFILNI+KORISHLAR+SONI' alt=''/> </div>",unsafe_allow_html=True)