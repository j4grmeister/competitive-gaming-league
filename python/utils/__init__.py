import python.utils.cache
import python.utils.checks
import python.utils.config
import python.utils.database
import python.utils.security
import python.utils.teams
import python.utils.users
import python.utils.converters
import python.utils.selectors

import uuid

emoji_list = ['0⃣', '1⃣', '2⃣', '3⃣', '4⃣', '5⃣', '6⃣', '7⃣', '8⃣', '9⃣', '🔟', '🇦', '🇧', '🇨', '🇩', '🇪', '🇫', '🇬', '🇭', '🇮', '🇯', '🇰', '🇱', '🇲', '🇳', '🇴', '🇵']
emoji_confirm = '✅'
emoji_decline = '❌'

def generate_id():
    return uuid.uuid1().hex
