"""Word-problem set for the reasoning tasks (R1-R3), with exact ground truth.

Each problem is defined by a canonical step decomposition. A step is a dict:
  {"desc": str, "op": "add"|"sub"|"mul"|"div",
   "args": [("n", <number in the problem text>) | ("s", <index of earlier step>)]}

The exact solver evaluates the decomposition, so the gold answer and every
gold intermediate value are known exactly. That is what lets the lab measure
a reasoner instead of merely admiring its prose -- and what gives R3's
verifier something exact to check against.

All problems are original to this lab (print shop, community hall, courier,
theatre, warehouse, ...). None is taken from the companion research report.
"""

from __future__ import annotations


def _step(desc, op, *args):
    return {"desc": desc, "op": op, "args": list(args)}


def _n(v):
    return ("n", v)


def _s(i):
    return ("s", i)


PROBLEMS = [
    {
        "id": "p01_print_shop",
        "text": ("A print shop press prints 240 flyers per hour. An order needs "
                 "1,440 flyers, and the shop runs 2 presses at once on the order. "
                 "How many hours does the order take?"),
        "steps": [
            _step("Combined rate of 2 presses", "mul", _n(240), _n(2)),
            _step("Hours = flyers / rate", "div", _n(1440), _s(0)),
        ],
    },
    {
        "id": "p02_hall_chairs",
        "text": ("A community hall has 14 rows of 16 chairs. For a concert, "
                 "148 chairs are filled. How many chairs are empty?"),
        "steps": [
            _step("Total chairs", "mul", _n(14), _n(16)),
            _step("Empty = total - filled", "sub", _s(0), _n(148)),
        ],
    },
    {
        "id": "p03_bookbinder",
        "text": ("A bookbinder is binding a 288-page book that is gathered in "
                 "signatures of 32 pages. Binding one book takes 6 minutes of "
                 "sewing and 4 minutes of gluing. How many minutes does it take "
                 "to bind 5 books?"),
        "steps": [
            _step("Minutes per book", "add", _n(6), _n(4)),
            _step("Minutes for 5 books", "mul", _s(0), _n(5)),
        ],
    },
    {
        "id": "p04_courier_trips",
        "text": ("A courier van carries 26 parcels per trip. A depot must move "
                 "208 parcels. The van makes 4 trips before noon. How many trips "
                 "are still needed after noon?"),
        "steps": [
            _step("Total trips needed", "div", _n(208), _n(26)),
            _step("Trips after noon", "sub", _s(0), _n(4)),
        ],
    },
    {
        "id": "p05_theatre_change",
        "text": ("A theatre sells tickets for $9 each. A school books 7 rows of "
                 "12 seats and pays with a $1,000 voucher. How much change is due?"),
        "steps": [
            _step("Seats booked", "mul", _n(7), _n(12)),
            _step("Cost of the seats", "mul", _s(0), _n(9)),
            _step("Change from the voucher", "sub", _n(1000), _s(1)),
        ],
    },
    {
        "id": "p06_warehouse_bottles",
        "text": ("A warehouse packs 6 bottles per box and 8 boxes per crate. An "
                 "order is for 30 crates, and 5 crates are already packed. How "
                 "many bottles still need to be packed?"),
        "steps": [
            _step("Bottles per crate", "mul", _n(6), _n(8)),
            _step("Crates still to pack", "sub", _n(30), _n(5)),
            _step("Bottles still to pack", "mul", _s(0), _s(1)),
        ],
    },
    {
        "id": "p07_garden_seedlings",
        "text": ("A garden centre sells seedlings in trays of 12. A gardener buys "
                 "9 trays and plants 86 seedlings. How many seedlings are left "
                 "unplanted?"),
        "steps": [
            _step("Seedlings bought", "mul", _n(9), _n(12)),
            _step("Left unplanted", "sub", _s(0), _n(86)),
        ],
    },
    {
        "id": "p08_library_net",
        "text": ("A library lends out 35 books per day. Over 6 days, 49 of the "
                 "lent books are also returned. How many more books are out than "
                 "came back, in total, over the 6 days?"),
        "steps": [
            _step("Books lent in 6 days", "mul", _n(35), _n(6)),
            _step("Net books out", "sub", _s(0), _n(49)),
        ],
    },
    {
        "id": "p09_cycling_club",
        "text": ("A cycling club rides 24 km on Saturday and 31 km on Sunday, "
                 "every weekend. How many kilometres does the club ride in "
                 "6 weekends?"),
        "steps": [
            _step("Kilometres per weekend", "add", _n(24), _n(31)),
            _step("Kilometres in 6 weekends", "mul", _s(0), _n(6)),
        ],
    },
    {
        "id": "p10_aquarium_tickets",
        "text": ("Aquarium tickets cost $14 each. A family buys 6 tickets. "
                 "How much do they pay?"),
        "steps": [
            _step("Total cost", "mul", _n(14), _n(6)),
        ],
    },
    {
        "id": "p11_farm_cartons",
        "text": ("A farm stand collects 132 eggs and packs them in cartons of "
                 "12 eggs. It then sells 7 cartons. How many cartons remain?"),
        "steps": [
            _step("Cartons packed", "div", _n(132), _n(12)),
            _step("Cartons remaining", "sub", _s(0), _n(7)),
        ],
    },
    {
        "id": "p12_workshop_chairs",
        "text": ("A workshop makes 18 chairs per week. It has an order for "
                 "144 chairs. After 5 weeks, the customer increases the order "
                 "by 36 chairs. How many more weeks does the workshop need to "
                 "finish the order?"),
        "steps": [
            _step("Chairs made in 5 weeks", "mul", _n(18), _n(5)),
            _step("Total chairs now ordered", "add", _n(144), _n(36)),
            _step("Chairs still to make", "sub", _s(1), _s(0)),
            _step("More weeks needed", "div", _s(2), _n(18)),
        ],
    },
    {
        "id": "p13_raffle_boxes",
        "text": ("At a school fair, 240 raffle tickets are printed. Class A "
                 "sells 95 tickets and Class B sells 77 tickets. The unsold "
                 "tickets are split equally between 2 boxes. How many unsold "
                 "tickets go in each box?"),
        "steps": [
            _step("Tickets sold", "add", _n(95), _n(77)),
            _step("Tickets unsold", "sub", _n(240), _s(0)),
            _step("Unsold tickets per box", "div", _s(1), _n(2)),
        ],
    },
    {
        "id": "p14_caterer_trays",
        "text": ("A caterer prepares 380 sandwiches and packs them 10 to a "
                 "tray. 9 trays go to one event and 13 trays go to another. "
                 "How many trays remain?"),
        "steps": [
            _step("Trays packed", "div", _n(380), _n(10)),
            _step("Trays sent out", "add", _n(9), _n(13)),
            _step("Trays remaining", "sub", _s(0), _s(1)),
        ],
    },
]

_OPS = {
    "add": lambda a, b: a + b,
    "sub": lambda a, b: a - b,
    "mul": lambda a, b: a * b,
    "div": lambda a, b: a / b,
}


def evaluate_step(step, prior_values):
    """Evaluate one step exactly, given the values of the steps before it."""
    vals = []
    for kind, ref in step["args"]:
        vals.append(ref if kind == "n" else prior_values[ref])
    out = _OPS[step["op"]](vals[0], vals[1])
    return int(out) if float(out).is_integer() else out


def solve(problem):
    """Return (gold_step_values, gold_answer) for a problem."""
    values = []
    for st in problem["steps"]:
        values.append(evaluate_step(st, values))
    return values, values[-1]


def text_numbers(problem):
    """Numbers that literally appear in the problem text, in order."""
    import re

    return [float(x) if "." in x else int(x)
            for x in re.findall(r"\d[\d,]*", problem["text"].replace(",", ""))]


if __name__ == "__main__":
    for p in PROBLEMS:
        vals, ans = solve(p)
        print(f"{p['id']:24s} steps={len(p['steps'])} gold={vals} answer={ans}")
