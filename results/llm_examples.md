# Real-model example chains (verbatim)

Model: Qwen/Qwen2.5-0.5B-Instruct on CPU. Seed 1234, temperature 0.7, k=9 sampled chains per problem, greedy direct answers. Extracted answers are the lab's parser's reading of each completion; unparseable counts as wrong. Headline results: direct 0/14, single chain 6/14, majority vote 9/14, verifier best-of-9 5/14.

## Direct answer fails, chain-of-thought succeeds

Direct output (greedy, extracted answer: 20; gold: 76):

```text
20
```

The first sampled chain:

> Problem: A community hall has 14 rows of 16 chairs. For a concert, 148 chairs are filled. How many chairs are empty?
>
> Chain #0 (extracted answer: 76; gold: 76):

```text
To determine how many chairs are empty in the community hall after the concert, we need to follow these steps:

1. Calculate the total number of chairs in the hall.
2. Subtract the number of chairs that were filled from the total number of chairs.

**Step 1: Calculate the total number of chairs**

The community hall has 14 rows of chairs, and each row contains 16 chairs. Therefore, the total number of chairs is:
\[
14 \text{ rows} \times 16 \text{ chairs per row} = 224 \text{ chairs}
\]

**Step 2: Subtract the number of filled chairs from the total number of chairs**

After the concert, 148 chairs are filled. To find out how many chairs are left empty, we subtract the number of filled chairs from the total number of chairs:
\[
224 \text{ chairs} - 148 \text{ filled chairs} = 76 \text{ empty chairs}
\]

Thus, the number of empty chairs is:
\[
\boxed{76}
\]
```

## Self-consistency rescue: the first chain is wrong, the majority is right

Vote distribution over the 9 extracted answers: {'240': 1, '3': 6, '6': 2} -- the majority answer is 3 (6/9), which is correct.

The first chain (wrong):

> Problem: A print shop press prints 240 flyers per hour. An order needs 1,440 flyers, and the shop runs 2 presses at once on the order. How many hours does the order take?
>
> Chain #0 (extracted answer: 240; gold: 3):

```text
To determine how long it takes for the order to be printed, we need to follow these steps:

1. **Calculate the number of sets of 240 flyers needed to make 1,440 flyers:**
   \[
   \text{Number of sets} = \frac{\text{Total number of flyers}}{\text{Fliers per set}} = \frac{1440}{240}
   \]
   Performing the division:
   \[
   \frac{1440}{240} = 6
   \]

2. **Determine the time required for one set of printing:**
   - The shop has two presses working simultaneously.
   - Each press can print 240 flyers per hour.
   - Therefore, together they can print \(2 \times 240\) flyers per hour.

3. **Calculate the total time required to print all 1,440 flyers in one set:**
   \[
   \text{Time per set} = \frac{\text{Total number of flyers}}{\text{Fliers per set}} = \frac{1440}{240}
   \]
   Performing the division:
   \
```

A chain that got it right:

> Problem: A print shop press prints 240 flyers per hour. An order needs 1,440 flyers, and the shop runs 2 presses at once on the order. How many hours does the order take?
>
> Chain #1 (extracted answer: 3; gold: 3):

```text
To determine how long it takes for the order to be printed using two presses simultaneously, we need to follow these steps:

1. **Calculate the total number of flyers that can be printed in one hour by both presses combined:**
   - Each press prints 240 flyers per hour.
   - There are two presses working together.

   Therefore, the total number of flyers printed per hour is:
   \[
   240 \text{ flyers/press} \times 2 \text{ presses} = 480 \text{ flyers/hour}
   \]

2. **Determine the time required to print all 1,440 flyers:**
   - We know that 480 flyers can be printed per hour.
   - The order requires 1,440 flyers.

   To find out how many hours it will take to print 1,440 flyers, we divide the total number of flyers by the number of flyers printed per hour:
   \[
   \frac{1,440 \text{ flyers}}{480 \text{ flyers/hour}} = 3 \text{ hours}
   \]

Therefore, the order will take \boxed{3} hours
```

## An honest failure: direct, vote and verifier all miss

Gold answer: 4. Direct answered 13; the majority vote was 4.095; the verifier's pick was 104. Wrong chains are data too -- this is what the failure looks like from inside.

The verifier's (wrong) pick:

> Problem: A courier van carries 26 parcels per trip. A depot must move 208 parcels. The van makes 4 trips before noon. How many trips are still needed after noon?
>
> Chain #4 (extracted answer: 104; gold: 4):

```text
To determine how many more trips the courier van needs to make, we can follow these steps:

1. Calculate the total number of parcels transported in 4 trips.
   - Each trip carries 26 parcels.
   - Therefore, in 4 trips, the total number of parcels is \( 26 \times 4 = 104 \).

2. Determine how many parcels are left to be delivered.
   - There were originally 208 parcels to deliver.
   - After 4 trips, there are \( 208 - 104 = 104 \) parcels remaining.

3. Calculate the number of additional trips required to deliver the remaining parcels.
   - Each trip requires 26 parcels.
   - To find out how many more trips are needed to deliver the remaining 104 parcels, we divide the remaining number of parcels by the number of parcels each trip delivers:
     \[
     \frac{104}{26} = 4 \text{ remainder } 10
     \]
   - This means that 4 trips will complete the delivery of the first 104 parcels (since \( 4 \times 26 = 104 \)), and
```

