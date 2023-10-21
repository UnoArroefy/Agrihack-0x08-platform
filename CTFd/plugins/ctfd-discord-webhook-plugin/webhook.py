from flask import request
from flask.wrappers import Response
from CTFd.utils.dates import ctftime
from CTFd.models import Challenges, Solves
from CTFd.utils import config as ctfd_config
from CTFd.utils.user import get_current_team, get_current_user
from discord_webhook import DiscordWebhook
from functools import wraps
from .config import config
from random import randint

import re
from urllib.parse import quote

ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(n//10%10!=1)*(n%10<4)*n%10::4])
sanreg = re.compile(r'(~|!|@|#|\$|%|\^|&|\*|\(|\)|\_|\+|\`|-|=|\[|\]|;|\'|,|\.|\/|\{|\}|\||:|"|<|>|\?)')
sanitize = lambda m: sanreg.sub(r'\1',m)

def load(app):
    config(app)
    TEAMS_MODE = ctfd_config.is_teams_mode()

    if not app.config['DISCORD_WEBHOOK_URL']:
        print("No DISCORD_WEBHOOK_URL set! Plugin disabled.")
        return
    def challenge_attempt_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            result = f(*args, **kwargs)
            if not ctftime():
                return result
            if isinstance(result, Response):
                data = result.json
                if isinstance(data, dict) and data.get("success") == True and isinstance(data.get("data"), dict) and data.get("data").get("status") == "correct":
                    if request.content_type != "application/json":
                        request_data = request.form
                    else:
                        request_data = request.get_json()
                    challenge_id = request_data.get("challenge_id")
                    challenge = Challenges.query.filter_by(id=challenge_id).first_or_404()
                    solvers = Solves.query.filter_by(challenge_id=challenge.id)
                    if TEAMS_MODE:
                        solvers = solvers.filter(Solves.team.has(hidden=False))
                    else:
                        solvers = solvers.filter(Solves.user.has(hidden=False))
                    num_solves = solvers.count()

                    limit = app.config["DISCORD_WEBHOOK_LIMIT"]
                    if int(limit) > 0 and num_solves > int(limit):
                        return result
                    webhook = DiscordWebhook(url=app.config['DISCORD_WEBHOOK_URL'])

                    user = get_current_user()

                    random_text = [
                        "Ngeri banget bang",
                        "Gada Obat!",
                        "Jaoggg",
                        "No Medicine Sir",
                        "Emang boleh sejago itu??",
                        "Tinki Winky Dipsi Lala Puh Sepuh",
                        "Kata orangnya terlalu mudah",
                        "Bang udah bang"
                    ]

                    random_emoji = [
                        ":cold_face:",
                        ":drop_of_blood:",
                        ":sunglasses:",
                        ":first_place:",
                        ":hot_face:",
                        ":sparkles:",
                        ":man_bowing:",
                    ]

                    prefix = random_text[randint(0,10) % len(random_text)]
                    suffix = random_emoji[randint(0,10) % len(random_emoji)]
                    message = f"{prefix}, first blood for challenge **{sanitize(challenge.name)}** from {sanitize(user.name)} {suffix}"
                    webhook.content = message
                    webhook.execute()
            return result
        return wrapper

    app.view_functions['api.challenges_challenge_attempt'] = challenge_attempt_decorator(app.view_functions['api.challenges_challenge_attempt'])