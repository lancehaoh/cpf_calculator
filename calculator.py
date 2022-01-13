import config
from state import State

config = config.load()
state = State(config)

while state.age < 55:
    state.advance()
    print(state)
