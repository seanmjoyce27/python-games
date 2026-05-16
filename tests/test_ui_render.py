"""
Smoke tests for roadmap UI affordances rendered by the game page.
"""


def test_game_page_renders_learning_controls(client, test_game):
    response = client.get(f'/game/{test_game}?user_id=1')

    assert response.status_code == 200
    html = response.data.decode('utf-8')

    assert 'id="sandboxBtn"' in html
    assert 'id="pairModeBtn"' in html
    assert 'id="shareBtn"' in html
    assert 'id="syntaxRescue"' in html
    assert 'id="celebrationModal"' in html
    assert 'id="snapshotModal"' in html
    assert 'getMissionRoadmapHtml' in html
    assert 'speakText' in html
