import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from models import db, User, SocialLink, ProfileLink, ThemeSetting

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")

# Configuração do banco de dados
# Verificar se DATABASE_URL está definido, caso contrário usar SQLite
db_url = os.environ.get("DATABASE_URL")
if db_url is None:
    db_url = "sqlite:///linkstack.db"
    print("Aviso: Variável de ambiente DATABASE_URL não encontrada. Usando SQLite local.")

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Inicializar o banco de dados
db.init_app(app)

# Criar tabelas
with app.app_context():
    db.create_all()
    
    # Verificar se existe um usuário de demonstração, caso contrário, criar
    demo_user = User.query.filter_by(username='demo').first()
    if not demo_user:
        demo_user = User(
            username='demo',
            email='demo@linkstack.com',
            name='Augusto Araujo',
            bio='Desenvolvedor & entusiasta de IA',
            phone='(98) 98100-0099'
        )
        demo_user.set_password('demo1234')
        
        # Adicionar perfil social
        social_links = [
            SocialLink(platform='instagram', url='https://www.instagram.com/augu_ia/', icon='fa-instagram'),
            SocialLink(platform='linkedin', url='#', icon='fa-linkedin'),
            SocialLink(platform='github', url='#', icon='fa-github'),
            SocialLink(platform='twitter', url='#', icon='fa-twitter')
        ]
        demo_user.social_links = social_links
        
        # Adicionar links do perfil
        profile_links = [
            ProfileLink(title='Meu Portfolio', url='#', icon='fa-globe', css_class='website', position=1),
            ProfileLink(title='Projetos de IA', url='#', icon='fa-code', css_class='store', position=2),
            ProfileLink(title='Fale Comigo', url='#', icon='fa-envelope', css_class='contact', position=3)
        ]
        demo_user.profile_links = profile_links
        
        # Adicionar configurações de tema
        theme_settings = ThemeSetting(theme_name='theme-2')
        demo_user.theme_settings = theme_settings
        
        db.session.add(demo_user)
        db.session.commit()

@app.route('/')
def index():
    # Obter o usuário demo (por enquanto só temos esse)
    user = User.query.filter_by(username='demo').first_or_404()
    
    # Montar o perfil a partir dos dados do usuário
    profile = {
        'name': user.name,
        'bio': user.bio,
        'phone': user.phone,
        'social_links': [
            {
                'platform': link.platform, 
                'url': link.url, 
                'icon': link.icon
            } for link in user.social_links
        ],
        'links': [
            {
                'title': link.title, 
                'url': link.url, 
                'icon': link.icon, 
                'class': link.css_class
            } for link in user.profile_links
        ]
    }
    
    # Obter o tema atual
    theme = 'theme-2'  # Tema padrão
    if user.theme_settings:
        theme = user.theme_settings.theme_name
    
    return render_template('index.html', profile=profile, theme=theme)

@app.route('/update-profile', methods=['POST'])
def update_profile():
    try:
        # Obter dados do formulário
        data = request.json
        
        # Obter usuário (usamos o demo por enquanto)
        user = User.query.filter_by(username='demo').first_or_404()
        
        # Atualizar dados do usuário
        user.name = data.get('name')
        user.bio = data.get('bio')
        user.phone = data.get('phone')
        
        # Atualizar links sociais
        # Primeiro, remover todos os links existentes
        for link in user.social_links:
            db.session.delete(link)
        
        # Adicionar os novos links sociais
        for link_data in data.get('social_links', []):
            social_link = SocialLink(
                user_id=user.id,
                platform=link_data.get('platform'),
                url=link_data.get('url'),
                icon=link_data.get('icon')
            )
            db.session.add(social_link)
        
        # Atualizar links do perfil
        # Primeiro, remover todos os links existentes
        for link in user.profile_links:
            db.session.delete(link)
        
        # Adicionar os novos links do perfil
        for index, link_data in enumerate(data.get('profile_links', [])):
            profile_link = ProfileLink(
                user_id=user.id,
                title=link_data.get('title'),
                url=link_data.get('url'),
                icon=link_data.get('icon'),
                css_class=link_data.get('class'),
                position=index + 1
            )
            db.session.add(profile_link)
        
        # Salvar as alterações no banco de dados
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Perfil atualizado com sucesso!'})
    except Exception as e:
        db.session.rollback()
        print(f'Erro ao atualizar perfil: {str(e)}')
        return jsonify({'success': False, 'message': f'Erro ao atualizar o perfil: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
