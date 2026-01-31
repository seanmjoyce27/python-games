"""
Tests for API endpoints
"""
import pytest
import json


class TestUserAPI:
    """Tests for user management API"""

    def test_get_users_empty(self, client):
        """Test getting users when none exist (except fixture)"""
        response = client.get('/api/users')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)

    def test_create_user(self, client):
        """Test creating a new user"""
        response = client.post('/api/users',
                               json={'username': 'alice'},
                               content_type='application/json')
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['username'] == 'alice'
        assert 'id' in data

    def test_create_user_short_name(self, client):
        """Test creating user with too short name"""
        response = client.post('/api/users',
                               json={'username': 'a'},
                               content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_create_duplicate_user(self, client):
        """Test creating duplicate username"""
        client.post('/api/users', json={'username': 'bob'},
                    content_type='application/json')
        response = client.post('/api/users', json={'username': 'bob'},
                               content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'already exists' in data['error'].lower()


class TestGameAPI:
    """Tests for game API"""

    def test_get_games(self, client):
        """Test getting all games"""
        response = client.get('/api/games')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) >= 1  # At least test game


class TestCodeAPI:
    """Tests for code version API"""

    def test_load_code_template(self, client, test_user, test_game):
        """Test loading code when no saves exist"""
        response = client.post('/api/code/load',
                               json={'user_id': test_user, 'game_id': test_game},
                               content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'code' in data
        assert data['version_id'] is None

    def test_save_code(self, client, test_user, test_game):
        """Test saving code"""
        code = 'print("Hello, World!")'
        response = client.post('/api/code/save',
                               json={
                                   'user_id': test_user,
                                   'game_id': test_game,
                                   'code': code,
                                   'message': 'First save',
                                   'is_checkpoint': True
                               },
                               content_type='application/json')
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'version_id' in data
        assert data['message'] == 'Code saved successfully'

    def test_save_no_changes(self, client, test_user, test_game):
        """Test saving when code hasn't changed"""
        code = 'print("test")'

        # First save
        client.post('/api/code/save',
                    json={'user_id': test_user, 'game_id': test_game, 'code': code},
                    content_type='application/json')

        # Second save with same code
        response = client.post('/api/code/save',
                               json={'user_id': test_user, 'game_id': test_game, 'code': code},
                               content_type='application/json')

        data = json.loads(response.data)
        assert 'No changes detected' in data['message']

    def test_load_saved_code(self, client, test_user, test_game):
        """Test loading previously saved code"""
        code = 'print("Loaded code")'

        # Save code first
        client.post('/api/code/save',
                    json={'user_id': test_user, 'game_id': test_game, 'code': code},
                    content_type='application/json')

        # Load it back
        response = client.post('/api/code/load',
                               json={'user_id': test_user, 'game_id': test_game},
                               content_type='application/json')

        data = json.loads(response.data)
        assert data['code'] == code
        assert data['version_id'] is not None

    def test_get_history_empty(self, client, test_user, test_game):
        """Test getting history when no saves exist"""
        response = client.post('/api/code/history',
                               json={'user_id': test_user, 'game_id': test_game},
                               content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['total'] == 0
        assert len(data['versions']) == 0

    def test_get_history(self, client, test_user, test_game):
        """Test getting version history"""
        # Create multiple saves
        for i in range(5):
            client.post('/api/code/save',
                        json={
                            'user_id': test_user,
                            'game_id': test_game,
                            'code': f'print({i})',
                            'message': f'Save {i}'
                        },
                        content_type='application/json')

        # Get history
        response = client.post('/api/code/history',
                               json={'user_id': test_user, 'game_id': test_game},
                               content_type='application/json')
        data = json.loads(response.data)

        assert data['total'] == 5
        assert len(data['versions']) == 5
        assert data['has_more'] is False

    def test_get_history_pagination(self, client, test_user, test_game):
        """Test history pagination"""
        # Create 10 saves
        for i in range(10):
            client.post('/api/code/save',
                        json={
                            'user_id': test_user,
                            'game_id': test_game,
                            'code': f'print({i})'
                        },
                        content_type='application/json')

        # Get first page (limit 5)
        response = client.post('/api/code/history',
                               json={
                                   'user_id': test_user,
                                   'game_id': test_game,
                                   'limit': 5,
                                   'offset': 0
                               },
                               content_type='application/json')
        data = json.loads(response.data)

        assert data['total'] == 10
        assert len(data['versions']) == 5
        assert data['has_more'] is True

        # Get second page
        response = client.post('/api/code/history',
                               json={
                                   'user_id': test_user,
                                   'game_id': test_game,
                                   'limit': 5,
                                   'offset': 5
                               },
                               content_type='application/json')
        data = json.loads(response.data)

        assert len(data['versions']) == 5
        assert data['has_more'] is False

    def test_get_version(self, client, test_code_version):
        """Test getting a specific version"""
        response = client.get(f'/api/code/version/{test_code_version}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'code' in data
        assert 'message' in data
        assert data['id'] == test_code_version

    def test_restore_version(self, client, test_user, test_game):
        """Test restoring an old version"""
        # Create initial save
        code1 = 'print("version 1")'
        response = client.post('/api/code/save',
                               json={
                                   'user_id': test_user,
                                   'game_id': test_game,
                                   'code': code1
                               },
                               content_type='application/json')
        version1_id = json.loads(response.data)['version_id']

        # Create second save
        code2 = 'print("version 2")'
        client.post('/api/code/save',
                    json={
                        'user_id': test_user,
                        'game_id': test_game,
                        'code': code2
                    },
                    content_type='application/json')

        # Restore first version
        response = client.post(f'/api/code/restore/{version1_id}',
                               json={'user_id': test_user},
                               content_type='application/json')

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['code'] == code1
        assert 'restored' in data['message'].lower()

    def test_diff_versions(self, client, test_user, test_game):
        """Test getting diff between versions"""
        # Create two versions
        code1 = 'print("hello")'
        response1 = client.post('/api/code/save',
                                json={'user_id': test_user, 'game_id': test_game, 'code': code1},
                                content_type='application/json')
        v1_id = json.loads(response1.data)['version_id']

        code2 = 'print("hello world")'
        response2 = client.post('/api/code/save',
                                json={'user_id': test_user, 'game_id': test_game, 'code': code2},
                                content_type='application/json')
        v2_id = json.loads(response2.data)['version_id']

        # Get diff
        response = client.post('/api/code/diff',
                               json={'version1_id': v1_id, 'version2_id': v2_id},
                               content_type='application/json')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'diff' in data
        assert isinstance(data['diff'], list)


class TestRoutes:
    """Tests for page routes"""

    def test_index_page(self, client):
        """Test index page loads"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Python Game Builder' in response.data

    def test_game_page(self, client, test_game):
        """Test game page loads"""
        response = client.get(f'/game/{test_game}')
        assert response.status_code == 200
        assert b'Code Editor' in response.data or b'Test Snake' in response.data

    def test_game_not_found(self, client):
        """Test 404 for non-existent game"""
        response = client.get('/game/999')
        assert response.status_code == 404
