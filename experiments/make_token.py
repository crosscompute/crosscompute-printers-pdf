from crosscompute_platform.routines.token import make_token
from crosscompute_tokens import set_tokens_backend


set_tokens_backend('redis')
token = make_token(['echoes'], ['print input'])
print(token)
