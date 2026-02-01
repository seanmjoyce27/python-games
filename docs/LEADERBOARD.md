# 🏆 Mission Leaderboard

The leaderboard displays which coders have completed the most missions, creating friendly competition and motivation.

## Features

### Visual Ranking
- **Medal System**: Top 3 coders get special medals (🥇 🥈 🥉)
- **Numeric Ranking**: All other positions show their rank number
- **Avatar Display**: Shows each coder's avatar emoji and color
- **Mission Count**: Displays total completed missions

### Design Elements
- **Top 3 Highlight**: Special golden background and border for podium positions
- **Responsive Layout**: Adapts to mobile and tablet screens
- **Real-time Updates**: Refreshes when page loads
- **Hover Effects**: Interactive feedback on leaderboard entries

## How It Works

### Ranking Logic
1. Counts completed missions for each user
2. Sorts users by completion count (highest first)
3. Assigns ranks based on position

### Display Format
```
🥇 | 🚀 | Astral Compiler        | 15 missions
🥈 | 🤖 | Coremind Architect     | 12 missions  
🥉 | 🐍 | Dynamic Coil           | 8 missions
#4 | 👾 | Event Horizon...       | 5 missions
```

## API Endpoint

**GET** `/api/leaderboard`

Returns array of users sorted by completed missions:
```json
[
  {
    "user_id": 2,
    "avatar": {
      "id": 2,
      "name": "Astral Compiler",
      "emoji": "🚀",
      "color": "#E94B3C"
    },
    "completed_missions": 15
  },
  ...
]
```

## Styling

### Desktop View
- Grid layout: Rank | Avatar | Name | Score
- Large medals for top 3
- Smooth hover animations

### Mobile View
- Compact rank and avatar
- Score moves below name
- Smaller font sizes
- Touch-friendly spacing

## Motivation System

The leaderboard creates positive competition by:
- **Recognition**: Top performers get special medals
- **Progress Visibility**: Everyone can see their standing
- **Goal Setting**: Clear target to reach next rank
- **Kid-Friendly**: No elimination, everyone stays on the board

## Technical Details

### Database Query
```python
completed_count = UserMissionProgress.query.filter_by(
    user_id=user.id,
    status='completed'
).count()
```

### Frontend Loading
```javascript
async function loadLeaderboard() {
    const response = await fetch('/api/leaderboard');
    const leaderboard = await response.json();
    // Render leaderboard entries...
}
```

## Empty State

When no users exist yet:
> "No coders yet! Complete missions to climb the leaderboard."

## Future Enhancements (Optional)

- Live updates when missions are completed
- Weekly/monthly leaderboards
- Badges for achievements
- Mission streaks
- Team competitions
