from arclet.alconna import Alconna, Args, Option, store_false
import src.arclet.alconna.notation as alcon

alc = Alconna(
    "test",
    Args["foo", str]["bar", int],
    Option("--spam|-s", default=True, action=store_false),
    Option("--eggs|-e", Args["count", int], default=0),
)

print(alcon.dumps(alc))


alc1 = alcon.loads(
"""\
namespace = test
command = test
args {
    foo = str
    bar = int
}
options = [
    {
        name = --spam
        aliases = [-s]
        default = true
        action = store_false
    }
    {
        name = --eggs
        aliases = [-e]
        args {
            count = int
        }
        default = 0
    }
]
"""
)
print(alc1)