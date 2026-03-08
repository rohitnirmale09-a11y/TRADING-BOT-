from SmartApi import SmartConnect
import config
import pyotp


def angel_login():

    print("\nConnecting to Angel One...")

    smartApi = SmartConnect(api_key=config.API_KEY)

    # Generate TOTP
    totp = pyotp.TOTP(config.TOTP_SECRET)
    otp = totp.now()

    # Create session
    session = smartApi.generateSession(
        config.CLIENT_ID,
        config.PASSWORD,
        otp
    )

    if not session["status"]:
        print("Login Failed ❌")
        exit()


    return smartApi