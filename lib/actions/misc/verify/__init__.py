
class VerifyActions:
    def __init__(self, client):
        from lib.actions.misc.verify.phone import PhoneVerify
        self.phone = PhoneVerify(client)
