# example_usage.py
from aggregator import Aggregator
from langchain_gigachat.embeddings.gigachat import GigaChatEmbeddings

def main():
    # Example JSON with service descriptions
    service_descriptions = {
        "AuthService": "Сервис аутентификации пользователей. Поддерживает регистрацию, вход, восстановление пароля и выход из системы. Использует JWT-токены для авторизации.",
        "PaymentService": "Сервис обработки платежей. Поддерживает различные платежные системы, включая банковские карты, электронные кошельки и криптовалюты. Обеспечивает защищенные транзакции.",
        "NotificationService": "Сервис уведомлений пользователей. Поддерживает отправку уведомлений по email, SMS, push-уведомления. Позволяет настраивать шаблоны и правила отправки.",
        "StorageService": "Сервис для хранения файлов и данных. Поддерживает загрузку, скачивание и обработку файлов различных форматов. Обеспечивает надежное хранение с резервным копированием."
    }
    
    # Example code, requirements, tests, and documentation
    requirements_text = """
    Требуется разработать API для работы с пользователями:
    1. Система должна обеспечивать регистрацию пользователей с email и паролем
    2. Должна быть возможность авторизации с использованием JWT-токенов
    3. Пользователи должны иметь возможность обновлять свои профили
    4. Система должна отправлять уведомления пользователям при важных событиях
    5. API должно поддерживать выполнение платежных операций
    """
    
    code_text = """
    from flask import Flask, request, jsonify
    import jwt
    from datetime import datetime, timedelta
    
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret_key'
    users_db = {}
    
    @app.route('/register', methods=['POST'])
    def register():
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
            
        if email in users_db:
            return jsonify({'error': 'User already exists'}), 400
            
        users_db[email] = {
            'password': password,
            'profile': {'name': '', 'age': 0}
        }
        
        return jsonify({'message': 'User registered successfully'}), 201
        
    @app.route('/login', methods=['POST'])
    def login():
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if email not in users_db or users_db[email]['password'] != password:
            return jsonify({'error': 'Invalid credentials'}), 401
            
        token = jwt.encode({
            'user': email,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, app.config['SECRET_KEY'])
        
        return jsonify({'token': token}), 200
        
    @app.route('/profile', methods=['PUT'])
    def update_profile():
        token = request.headers.get('Authorization')
        
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            email = payload['user']
            
            data = request.get_json()
            users_db[email]['profile'].update(data)
            
            return jsonify({'message': 'Profile updated successfully'}), 200
        except:
            return jsonify({'error': 'Invalid token'}), 401
    
    if __name__ == '__main__':
        app.run(debug=True)
    """
    
    test_cases_text = """
    import pytest
    from app import app
    import json
    
    @pytest.fixture
    def client():
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
            
    def test_register(client):
        response = client.post('/register', 
                             json={'email': 'test@example.com', 'password': 'password123'})
        assert response.status_code == 201
        
    def test_login(client):
        # Register user first
        client.post('/register', json={'email': 'test@example.com', 'password': 'password123'})
        
        # Then login
        response = client.post('/login', json={'email': 'test@example.com', 'password': 'password123'})
        assert response.status_code == 200
        assert 'token' in json.loads(response.data)
        
    def test_update_profile(client):
        # Register and login user
        client.post('/register', json={'email': 'test@example.com', 'password': 'password123'})
        login_response = client.post('/login', json={'email': 'test@example.com', 'password': 'password123'})
        token = json.loads(login_response.data)['token']
        
        # Update profile
        response = client.put('/profile', 
                            json={'name': 'Test User', 'age': 30},
                            headers={'Authorization': token})
        assert response.status_code == 200
    """
    
    documentation_text = """
    # API Documentation
    
    ## Authentication
    
    The API uses JWT tokens for authentication. To get a token, register a user and then log in.
    
    ## Endpoints
    
    ### POST /register
    Register a new user with email and password.
    
    ### POST /login
    Login with email and password to receive a JWT token.
    
    ### PUT /profile
    Update user profile. Requires authentication token in the Authorization header.
    """
    
    # Create the aggregator with service descriptions
    aggregator = Aggregator()
    
    # Run the analysis with the service descriptions
    report, bug_estimation = aggregator.aggregate(
        requirements_text, 
        code_text, 
        test_cases_text, 
        documentation_text,
        service_descriptions=service_descriptions
    )
    
    # Print the report
    print(report)
    
    # Print bug estimation summary
    print(f"\nОбщее количество потенциальных багов: {bug_estimation['bug_count']}")

if __name__ == "__main__":
    main() 