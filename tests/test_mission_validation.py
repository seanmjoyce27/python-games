"""
Tests for mission validation rules that protect beginner lessons from
passing because of starter-code scaffolding.
"""
import json


def create_mission(db, Mission, game_id, title, validation_type, validation_data):
    mission = Mission(
        game_id=game_id,
        title=title,
        description='Test mission',
        order=1,
        difficulty='beginner',
        validation_type=validation_type,
        validation_data=json.dumps(validation_data),
        hints='[]'
    )
    db.session.add(mission)
    db.session.commit()
    return mission


def test_comment_mission_requires_the_new_comment(client, app, test_user, test_game):
    from app import db, Mission

    mission = create_mission(db, Mission, test_game, 'Comment Mission', 'code_contains', {
        'text': '# This is my robot',
        'success_message': 'ok',
        'failure_message': 'missing'
    })

    starter_code = '# Mission 1: Python Basics\n# Existing starter notes\n'
    response = client.post(
        f'/api/missions/{mission.id}/validate',
        json={'user_id': test_user, 'code': starter_code},
        content_type='application/json'
    )
    data = json.loads(response.data)
    assert data['success'] is False

    response = client.post(
        f'/api/missions/{mission.id}/validate',
        json={'user_id': test_user, 'code': starter_code + '# This is my robot\n'},
        content_type='application/json'
    )
    data = json.loads(response.data)
    assert data['success'] is True


def test_string_variable_mission_does_not_match_robot_name(client, app, test_user, test_game):
    from app import db, Mission

    mission = create_mission(db, Mission, test_game, 'Name Mission', 'code_pattern', {
        'pattern': r'^name\s*=\s*[\'"][^\'"]+[\'"]\s*$',
        'success_message': 'ok',
        'failure_message': 'missing'
    })

    response = client.post(
        f'/api/missions/{mission.id}/validate',
        json={'user_id': test_user, 'code': 'robot_name = "Robo-01"\n'},
        content_type='application/json'
    )
    data = json.loads(response.data)
    assert data['success'] is False

    response = client.post(
        f'/api/missions/{mission.id}/validate',
        json={'user_id': test_user, 'code': 'robot_name = "Robo-01"\nname = "Robo"\n'},
        content_type='application/json'
    )
    data = json.loads(response.data)
    assert data['success'] is True
