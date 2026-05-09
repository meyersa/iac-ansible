from ansible.plugins.lookup import LookupBase

class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):
        key = terms[0]

        # direct lookup from Ansible vars (Vault already decrypted)
        value = variables.get(key)

        if value is None:
            raise Exception(f"Secret not found: {key}")

        return [value]