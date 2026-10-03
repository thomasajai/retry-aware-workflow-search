# MathQA: 200 test questions

Random sample without replacement, seed 42. Source indices are zero-based. All source text is preserved.

## 1. mathqa_test_0002

Category: physics | Source: test.json, index 2

there are 28 stations between hyderabad and bangalore . how many second class tickets have to be printed , so that a passenger can travel from any station to any other station ?

- **a)** 156
- **b)** 167
- **c)** 870
- **d)** 352
- **e)** 380

**Answer: c) 870**

**Original rationale**

"the total number of stations = 30 from 30 stations we have to choose any two stations and the direction of travel ( i . e . , hyderabad to bangalore is different from bangalore to hyderabad ) in 3 ⁰ p ₂ ways . 30 p ₂ = 30 * 29 = 870 . answer : c"

**Annotated formula**

```text
multiply(add(28, const_1), add(add(28, const_1), const_1))
```

**Linear formula**

```text
add(n0,const_1)|add(#0,const_1)|multiply(#0,#1)|
```

## 2. mathqa_test_0013

Category: general | Source: test.json, index 13

there are 1000 buildings in a street . a sign - maker is contracted to number the houses from 1 to 1000 . how many zeroes will he need ?

- **a)** 190
- **b)** 191
- **c)** 192
- **d)** 193
- **e)** 194

**Answer: c) 192**

**Original rationale**

divide as ( 1 - 100 ) ( 100 - 200 ) . . . . ( 900 - 1000 ) total 192 answer : c

**Annotated formula**

```text
add(add(divide(1000, const_10), multiply(subtract(const_10, 1), const_10)), const_2)
```

**Linear formula**

```text
divide(n0,const_10)|subtract(const_10,n1)|multiply(#1,const_10)|add(#0,#2)|add(#3,const_2)
```

## 3. mathqa_test_0026

Category: gain | Source: test.json, index 26

john and ingrid pay 30 % and 40 % tax annually , respectively . if john makes $ 60000 and ingrid makes $ 72000 , what is their combined tax rate ?

- **a)** 32 %
- **b)** 34.4 %
- **c)** 35 %
- **d)** 35.6 %
- **e)** 36.4 %

**Answer: d) 35.6 %**

**Original rationale**

"( 1 ) when 30 and 40 has equal weight or weight = 1 / 2 , the answer would be 35 . ( 2 ) when 40 has larger weight than 30 , the answer would be in between 35 and 40 . unfortunately , we have 2 answer choices d and e that fit that condition so we need to narrow down our range . ( 3 ) get 72000 / 132000 = 6 / 11 . 6 / 11 is a little above 6 / 12 = 1 / 2 . thus , our answer is just a little above 35 . answer : d"

**Annotated formula**

```text
multiply(divide(add(multiply(divide(30, const_100), 60000), multiply(divide(40, const_100), 72000)), add(72000, 60000)), const_100)
```

**Linear formula**

```text
add(n2,n3)|divide(n0,const_100)|divide(n1,const_100)|multiply(n2,#1)|multiply(n3,#2)|add(#3,#4)|divide(#5,#0)|multiply(#6,const_100)|
```

## 4. mathqa_test_0047

Category: general | Source: test.json, index 47

the maximum number of students among them 1345 pens and 775 pencils can be distributed in such a way that each student gets the same number of pens and same number of pencils is :

- **a)** 91
- **b)** 10
- **c)** 6
- **d)** 5
- **e)** none of these

**Answer: d) 5**

**Original rationale**

"explanation : required number of students = h . c . f of 1345 and 775 = 5 . answer : d"

**Annotated formula**

```text
gcd(1345, 775)
```

**Linear formula**

```text
gcd(n0,n1)|
```

## 5. mathqa_test_0079

Category: general | Source: test.json, index 79

an amount of rs . 1638 was divided among a , b and c , in the ratio 1 / 2 : 1 / 3 : 1 / 4 . find the share of a ?

- **a)** 656
- **b)** 456
- **c)** 756
- **d)** 745
- **e)** 720

**Answer: c) 756**

**Original rationale**

let the shares of a , b and c be a , b and c respectively . a : b : c = 1 / 2 : 1 / 3 : 1 / 4 let us express each term with a common denominator which is the last number divisible by the denominators of each term i . e . , 12 . a : b : c = 6 / 12 : 4 / 12 : 3 / 12 = 6 : 4 : 3 . share of a = 6 / 13 * 1638 = rs . 756 answer : c

**Annotated formula**

```text
multiply(divide(1638, add(add(2, 3), 4)), 4)
```

**Linear formula**

```text
add(n2,n4)|add(n6,#0)|divide(n0,#1)|multiply(n6,#2)
```

## 6. mathqa_test_0102

Category: physics | Source: test.json, index 102

there are 28 stations between ernakulam and chennai . how many second class tickets have to be printed , so that a passenger can travel from one station to any other station ?

- **a)** 800
- **b)** 820
- **c)** 850
- **d)** 870
- **e)** 900

**Answer: d) 870**

**Original rationale**

"the total number of stations = 30 from 30 stations we have to choose any two stations and the direction of travel ( ernakulam to chennai is different from chennai to ernakulam ) in 30 p 2 ways . 30 p 2 = 30 * 29 = 870 answer : d"

**Annotated formula**

```text
multiply(add(28, const_2), subtract(add(28, const_2), const_1))
```

**Linear formula**

```text
add(n0,const_2)|subtract(#0,const_1)|multiply(#0,#1)|
```

## 7. mathqa_test_0108

Category: gain | Source: test.json, index 108

if 5 % more is gained by selling an article for rs . 1000 than by selling it for rs . 20 , the cost of the article is ?

- **a)** 127
- **b)** 1600
- **c)** 1200
- **d)** 1680
- **e)** 1800

**Answer: b) 1600**

**Original rationale**

"let c . p . be rs . x . then , 5 % of x = 1000 - 20 = 80 x / 20 = 80 = > x = 1600 answer : b"

**Annotated formula**

```text
divide(subtract(1000, 20), divide(5, const_100))
```

**Linear formula**

```text
divide(n0,const_100)|subtract(n1,n2)|divide(#1,#0)|
```

## 8. mathqa_test_0122

Category: other | Source: test.json, index 122

at the faculty of aerospace engineering , 312 students study random - processing methods , 232 students study scramjet rocket engines and 112 students study them both . if every student in the faculty has to study one of the two subjects , how many students are there in the faculty of aerospace engineering ?

- **a)** 424 .
- **b)** 428 .
- **c)** 430 .
- **d)** 432 .
- **e)** 436

**Answer: d) 432 .**

**Original rationale**

"students studying random - processing methods = 312 students studying scramjet rocket engines = 232 students studying them both = 112 therefore ; students studying only random processing methods = 312 - 112 = 200 students studying only scramjet rocket engines = 232 - 112 = 120 students studying both = 112 students studying none = 0 ( as mentioned in question that every student in the faculty has to study one of the two subjects ) total students in faculty of aerospace engineering = students of only random processing methods + students of only scramjet rocket engines + both + none total number of students = 200 + 120 + 112 + 0 = 432 . . . . answer d"

**Annotated formula**

```text
add(subtract(312, divide(112, const_2)), subtract(232, divide(112, const_2)))
```

**Linear formula**

```text
divide(n2,const_2)|subtract(n0,#0)|subtract(n1,#0)|add(#1,#2)|
```

## 9. mathqa_test_0130

Category: physics | Source: test.json, index 130

if 8 men or 12 women can do a piece of work in 25 days , in how many days can the same work be done by 6 men and 11 women ?

- **a)** 10 days
- **b)** 11 days
- **c)** 13 days
- **d)** 15 days
- **e)** 17 days

**Answer: d) 15 days**

**Original rationale**

"8 men = 12 women ( i . e 2 men = 3 women ) 12 women 1 day work = 1 / 25 soln : 6 men ( 9 women ) + 11 women = 20 women = ? 1 women 1 day work = 12 * 25 = 1 / 300 so , 20 women work = 20 / 300 = 1 / 15 ans : 15 days answer : d"

**Annotated formula**

```text
inverse(add(divide(6, multiply(8, 25)), divide(11, multiply(12, 25))))
```

**Linear formula**

```text
multiply(n0,n2)|multiply(n1,n2)|divide(n3,#0)|divide(n4,#1)|add(#2,#3)|inverse(#4)|
```

## 10. mathqa_test_0131

Category: physics | Source: test.json, index 131

a train 140 meters long takes 6 seconds to cross a man walking at 5 kmph in the direction opposite to that of the train . find the speed of the train .

- **a)** 45 kmph
- **b)** 50 kmph
- **c)** 55 kmph
- **d)** 60 kmph
- **e)** 79 kmph

**Answer: e) 79 kmph**

**Original rationale**

"explanation : let the speed of the train be x kmph . speed of the train relative to man = ( x + 5 ) kmph = ( x + 5 ) × 5 / 18 m / sec . therefore 140 / ( ( x + 5 ) × 5 / 18 ) = 6 < = > 30 ( x + 5 ) = 2520 < = > x = 79 speed of the train is 79 kmph . answer : option e"

**Annotated formula**

```text
subtract(divide(140, multiply(6, const_0_2778)), 5)
```

**Linear formula**

```text
multiply(n1,const_0_2778)|divide(n0,#0)|subtract(#1,n2)|
```

## 11. mathqa_test_0177

Category: other | Source: test.json, index 177

a man invests some money partly in 9 % stock at 96 and partly in 12 % stock at 120 . to obtain equal dividends from both , he must invest the money in the ratio ?

- **a)** 16 : 18
- **b)** 16 : 13
- **c)** 16 : 15
- **d)** 16 : 12
- **e)** 16 : 11

**Answer: c) 16 : 15**

**Original rationale**

"for an income of re . 1 in 9 % stock at 96 , investment = rs . 96 / 9 = rs . 32 / 3 for an income re . 1 in 12 % stock at 120 , investment = rs . 120 / 12 = rs . 10 . ratio of investments = ( 32 / 3 ) : 10 = 32 : 30 = 16 : 15 answer : c"

**Annotated formula**

```text
divide(multiply(96, const_2), multiply(120, const_3))
```

**Linear formula**

```text
multiply(n1,const_2)|multiply(n3,const_3)|divide(#0,#1)|
```

## 12. mathqa_test_0187

Category: geometry | Source: test.json, index 187

a squirrel runs up a cylindrical post , in a perfect spiral path making one circuit for each rise of 3 feet . how many feet does the squirrel travels if the post is 18 feet tall and 3 feet in circumference ?

- **a)** 10 feet
- **b)** 12 feet
- **c)** 13 feet
- **d)** 15 feet
- **e)** 18 feet

**Answer: e) 18 feet**

**Original rationale**

"total circuit = 18 / 3 = 6 total feet squirrel travels = 6 * 3 = 18 feet answer : e"

**Annotated formula**

```text
multiply(divide(18, 3), 3)
```

**Linear formula**

```text
divide(n1,n0)|multiply(n2,#0)|
```

## 13. mathqa_test_0192

Category: physics | Source: test.json, index 192

in a 500 m race , the ratio of the speeds of two contestants a and b is 3 : 4 . a has a start of 155 m . then , a wins by :

- **a)** 60 m
- **b)** 20 m
- **c)** 40 m
- **d)** 20 m
- **e)** 23 m

**Answer: c) 40 m**

**Original rationale**

"to reach the winning post a will have to cover a distance of ( 500 - 155 ) m , i . e . , 345 m . while a covers 3 m , b covers 4 m . while a covers 345 m , b covers 4 x 345 / 3 m = 460 m . thus , when a reaches the winning post , b covers 460 m and therefore remains 40 m behind . a wins by 40 m . answer : c"

**Annotated formula**

```text
subtract(500, divide(multiply(subtract(500, 155), 4), 3))
```

**Linear formula**

```text
subtract(n0,n3)|multiply(n2,#0)|divide(#1,n1)|subtract(n0,#2)|
```

## 14. mathqa_test_0229

Category: general | Source: test.json, index 229

3 people candidates contested an election and they received 1136 , 7636 and 11628 votes respectively . what is the percentage of the total votes did the winning candidate get ?

- **a)** 40 %
- **b)** 45 %
- **c)** 57 %
- **d)** 58 %
- **e)** 60 %

**Answer: c) 57 %**

**Original rationale**

tot no of votes = ( 1136 + 7636 + 11628 ) = 20400 req = > ( 11628 / 20400 * 100 ) = > 57 % answer c

**Annotated formula**

```text
multiply(divide(11628, add(add(1136, 7636), 11628)), const_100)
```

**Linear formula**

```text
add(n1,n2)|add(n3,#0)|divide(n3,#1)|multiply(#2,const_100)
```

## 15. mathqa_test_0237

Category: general | Source: test.json, index 237

x and y are both integers . if x / y = 59.60 , then what is the sum of all the possible two digit remainders of x / y ?

- **a)** 560
- **b)** 315
- **c)** 672
- **d)** 900
- **e)** 1024

**Answer: b) 315**

**Original rationale**

"remainder = 0.60 - - > 60 / 100 - - > can be written as ( 60 / 4 ) / ( 100 / 4 ) = 15 / 25 so remainders can be 15 , 30 , 45 , 60 , . . . . . 90 . we need the sum of only 2 digit remainders - - > 15 + 30 + 45 + 60 + 75 + 90 = 315 answer : b"

**Annotated formula**

```text
add(multiply(divide(const_3, const_2), const_100), add(multiply(add(const_2, const_3), 59.60), const_3))
```

**Linear formula**

```text
add(const_2,const_3)|divide(const_3,const_2)|multiply(n0,#0)|multiply(#1,const_100)|add(#2,const_3)|add(#4,#3)|
```

## 16. mathqa_test_0260

Category: general | Source: test.json, index 260

the sum of ages of 5 children born at the intervals of 3 years each is 80 years . what is the age of the youngest child ?

- **a)** 3 years
- **b)** 4 years
- **c)** 6 years
- **d)** 7 years
- **e)** 10 years

**Answer: e) 10 years**

**Original rationale**

"let the ages of children be x , ( x + 3 ) , ( x + 6 ) , ( x + 9 ) and ( x + 12 ) years . then , x + ( x + 3 ) + ( x + 6 ) + ( x + 9 ) + ( x + 12 ) = 80 5 x = 50 x = 10 . age of the youngest child = x = 10 years . e )"

**Annotated formula**

```text
subtract(subtract(divide(80, 5), 3), 3)
```

**Linear formula**

```text
divide(n2,n0)|subtract(#0,n1)|subtract(#1,n1)|
```

## 17. mathqa_test_0271

Category: physics | Source: test.json, index 271

the length of minute hand of a clock is 5.6 cm . what is the area covered by this in 10 minutes

- **a)** 15.27
- **b)** 16.27
- **c)** 17.27
- **d)** 16.41
- **e)** 19.27

**Answer: d) 16.41**

**Original rationale**

area of circle is pi * r ^ 2 but in 10 minutes area covered is ( 10 / 60 ) * 360 = 60 degree so formula is pi * r ^ 2 * ( angle / 360 ) = 3.14 * ( 5.6 ^ 2 ) * ( 60 / 360 ) = 16.41 cm ^ 2 answer : d

**Annotated formula**

```text
multiply(divide(add(multiply(const_2, const_10), const_2), add(const_3, const_4)), multiply(multiply(5.6, 5.6), divide(multiply(const_1, const_60), multiply(const_100, const_3_6))))
```

**Linear formula**

```text
add(const_3,const_4)|multiply(const_10,const_2)|multiply(const_1,const_60)|multiply(const_100,const_3_6)|multiply(n0,n0)|add(#1,const_2)|divide(#2,#3)|divide(#5,#0)|multiply(#6,#4)|multiply(#7,#8)
```

## 18. mathqa_test_0283

Category: physics | Source: test.json, index 283

jane and ashley take 8 days and 40 days respectively to complete a project when they work on it alone . they thought if they worked on the project together , they would take fewer days to complete it . during the period that they were working together , jane took an eight day leave from work . this led to jane ' s working for four extra days on her own to complete the project . how long did it take to finish the project ?

- **a)** 14 days
- **b)** 15 days
- **c)** 16 days
- **d)** 18 days
- **e)** 20 days

**Answer: a) 14 days**

**Original rationale**

"let us assume that the work is laying 40 bricks . jane = 5 bricks per day ashley = 1 brick per day together = 6 bricks per day let ' s say first 8 days ashley works alone , no of bricks = 8 last 4 days jane works alone , no . of bricks = 20 remaining bricks = 40 - 28 = 12 so together , they would take 12 / 6 = 2 total no . of days = 8 + 4 + 2 = 14 answer is a"

**Annotated formula**

```text
add(add(divide(subtract(subtract(const_1, multiply(const_4, divide(const_1, 8))), multiply(add(const_4, const_4), divide(const_1, 40))), add(divide(const_1, 8), divide(const_1, 40))), add(const_4, const_4)), const_4)
```

**Linear formula**

```text
add(const_4,const_4)|divide(const_1,n0)|divide(const_1,n1)|add(#1,#2)|multiply(#1,const_4)|multiply(#0,#2)|subtract(const_1,#4)|subtract(#6,#5)|divide(#7,#3)|add(#0,#8)|add(#9,const_4)|
```

## 19. mathqa_test_0284

Category: general | Source: test.json, index 284

if an integer n is to be selected at random from 1 to 100 , inclusive , what is probability n ( n + 1 ) will be divisible by 32 ?

- **a)** 2 / 7
- **b)** 3 / 7
- **c)** 1 / 16
- **d)** 1 / 14
- **e)** 1 / 12

**Answer: c) 1 / 16**

**Original rationale**

"because n ( n + 1 ) is always an even product of even * odd or odd * even factors , there is a probability of 1 that that it will be divisible by 2 , and , thus , a probability of 1 / 2 that it will be divisible by 4 and , thus , a probability of 1 / 4 that it will be divisible by 8 and , thus , a probability of 1 / 8 that it will be divisible by 16 and , thus , a probability of 1 / 16 that it will be divisible by 32 1 * 1 / 16 = 1 / 16 answer : c"

**Annotated formula**

```text
divide(const_2, 32)
```

**Linear formula**

```text
divide(const_2,n3)|
```

## 20. mathqa_test_0292

Category: physics | Source: test.json, index 292

if the weight of 12 meters long rod is 13.4 kg . what is the weight of 6 meters long rod ?

- **a)** 6.7 kg .
- **b)** 10.8 kg .
- **c)** 12.4 kg .
- **d)** 18.0 kg
- **e)** none

**Answer: a) 6.7 kg .**

**Original rationale**

"answer ∵ weight of 12 m long rod = 13.4 kg ∴ weight of 1 m long rod = 13.4 / 12 kg ∴ weight of 6 m long rod = 13.4 x 6 / 12 = 6.7 kg option : a"

**Annotated formula**

```text
divide(multiply(6, 13.4), 12)
```

**Linear formula**

```text
multiply(n1,n2)|divide(#0,n0)|
```

## 21. mathqa_test_0322

Category: other | Source: test.json, index 322

a certain fraction has the same ratio to 1 / 36 , as 4 / 5 does to 2 / 9 . what is this certain fraction ?

- **a)** 1 / 5
- **b)** 1 / 10
- **c)** 1 / 15
- **d)** 1 / 20
- **e)** 1 / 25

**Answer: b) 1 / 10**

**Original rationale**

"x / ( 1 / 36 ) = ( 4 / 5 ) / ( 2 / 9 ) x = 4 * 9 * 1 / 36 * 5 * 2 = 1 / 10 the answer is b ."

**Annotated formula**

```text
divide(1, 36)
```

**Linear formula**

```text
divide(n0,n1)|
```

## 22. mathqa_test_0326

Category: other | Source: test.json, index 326

a group of people participate in some curriculum , 30 of them practice yoga , 20 study cooking , 15 study weaving , 5 of them study cooking only , 8 of them study both the cooking and yoga , 5 of them participate all curriculums . how many people study both cooking and weaving ?

- **a)** 1
- **b)** 2
- **c)** 3
- **d)** 4
- **e)** 5

**Answer: b) 2**

**Original rationale**

"both cooking and weaving = 20 - ( 5 + 8 + 5 ) = 2 so , the correct answer is b ."

**Annotated formula**

```text
subtract(subtract(subtract(20, 8), 5), 5)
```

**Linear formula**

```text
subtract(n1,n4)|subtract(#0,n5)|subtract(#1,n3)|
```

## 23. mathqa_test_0350

Category: general | Source: test.json, index 350

a student was asked to find 4 / 5 of a number . but the student divided the number by 4 / 5 , thus the student got 9 more than the correct answer . find the number .

- **a)** 16
- **b)** 18
- **c)** 20
- **d)** 22
- **e)** 24

**Answer: c) 20**

**Original rationale**

"let the number be x . ( 5 / 4 ) * x = ( 4 / 5 ) * x + 9 25 x = 16 x + 180 9 x = 180 x = 20 the answer is c ."

**Annotated formula**

```text
divide(divide(multiply(multiply(9, divide(4, 5)), divide(4, 5)), subtract(const_1, multiply(divide(4, 5), divide(4, 5)))), divide(4, 5))
```

**Linear formula**

```text
divide(n0,n1)|multiply(n4,#0)|multiply(#0,#0)|multiply(#0,#1)|subtract(const_1,#2)|divide(#3,#4)|divide(#5,#0)|
```

## 24. mathqa_test_0356

Category: general | Source: test.json, index 356

a man is 30 years older than his son . in two years , his age will be twice the age of his son . the present age of the son is

- **a)** 14 years
- **b)** 28 years
- **c)** 20 years
- **d)** 22 years
- **e)** none

**Answer: b) 28 years**

**Original rationale**

"solution let the son ' s present age be x years . then , man ' s present age = ( x + 30 ) years . then â € ¹ = â € º ( x + 30 ) + 2 = 2 ( x + 2 ) â € ¹ = â € º x + 32 = 2 x + 4 x = 28 . answer b"

**Annotated formula**

```text
divide(subtract(30, subtract(multiply(const_2, const_2), const_2)), subtract(const_2, const_1))
```

**Linear formula**

```text
multiply(const_2,const_2)|subtract(const_2,const_1)|subtract(#0,const_2)|subtract(n0,#2)|divide(#3,#1)|
```

## 25. mathqa_test_0372

Category: general | Source: test.json, index 372

what is the area inscribed by the lines y = 2 , x = 2 , y = 10 - x on an xy - coordinate plane ?

- **a)** a ) 8
- **b)** b ) 10
- **c)** c ) 12
- **d)** d ) 14
- **e)** e ) 18

**Answer: e) e ) 18**

**Original rationale**

first , let ' s graph the lines y = 2 and x = 2 at this point , we need to find the points where the line y = 10 - x intersects the other two lines . for the vertical line , we know that x = 2 , so we ' ll plug x = 2 into the equation y = 10 - x to get y = 10 - 2 = 8 perfect , when x = 2 , y = 8 , so one point of intersection is ( 28 ) for the horizontal line , we know that y = 2 , so we ' ll plug y = 2 into the equation y = 10 - x to get 2 = 10 - x . solve to get : x = 8 so , when y = 2 , x = 8 , so one point of intersection is ( 82 ) now add these points to our graph and sketch the line y = 10 - x at this point , we can see that we have the following triangle . the base has length 6 and the height is 6 area = ( 1 / 2 ) ( base ) ( height ) = ( 1 / 2 ) ( 6 ) ( 6 ) = 18 answer : e

**Annotated formula**

```text
multiply(subtract(subtract(10, 2), 2), multiply(multiply(const_2, const_0_25), subtract(subtract(10, 2), 2)))
```

**Linear formula**

```text
multiply(const_0_25,const_2)|subtract(n2,n0)|subtract(#1,n0)|multiply(#0,#2)|multiply(#3,#2)
```

## 26. mathqa_test_0379

Category: general | Source: test.json, index 379

when tossed , a certain coin has equal probability of landing on either side . if the coin is tossed 4 times , what is the probability that it will land twice on heads and twice tails ?

- **a)** 1 / 8
- **b)** 1 / 4
- **c)** 1 / 16
- **d)** 1 / 32
- **e)** 1 / 2

**Answer: c) 1 / 16**

**Original rationale**

must be twice on heads and twice on tails 1 / 2 * 1 / 2 * 1 / 2 * 1 / 2 = 1 / 16 answer : c

**Annotated formula**

```text
divide(const_1, power(const_2, 4))
```

**Linear formula**

```text
power(const_2,n0)|divide(const_1,#0)
```

## 27. mathqa_test_0383

Category: physics | Source: test.json, index 383

a can do a piece of work in 5 days and b can do it in 4 days how long will they both work together to complete the work ?

- **a)** 6 / 11
- **b)** 8 / 11
- **c)** 7 / 9
- **d)** 2 / 9
- **e)** 10 / 11

**Answer: d) 2 / 9**

**Original rationale**

"explanation : a ’ s one day work = 1 / 5 b ’ s one day work = 1 / 4 ( a + b ) ’ s one day work = 1 / 5 + 1 / 4 = 9 / 20 = > time = 20 / 9 = 2 2 / 9 days answer : option d"

**Annotated formula**

```text
divide(const_1, add(divide(const_1, 5), divide(const_1, 4)))
```

**Linear formula**

```text
divide(const_1,n0)|divide(const_1,n1)|add(#0,#1)|divide(const_1,#2)|
```

## 28. mathqa_test_0396

Category: physics | Source: test.json, index 396

two goods trains each 500 m long are running in opposite directions on parallel tracks . their speeds are 60 km / hr and 30 km / hr respectively . find the time taken by the slower train to pass the driver of the faster one ?

- **a)** 12 sec
- **b)** 24 sec
- **c)** 40 sec
- **d)** 60 sec
- **e)** 62 sec

**Answer: c) 40 sec**

**Original rationale**

"relative speed = 60 + 30 = 90 km / hr . 90 * 5 / 18 = 25 m / sec . distance covered = 500 + 500 = 1000 m . required time = 1000 / 25 = 40 sec . answer : c"

**Annotated formula**

```text
add(60, 30)
```

**Linear formula**

```text
add(n1,n2)|
```

## 29. mathqa_test_0413

Category: general | Source: test.json, index 413

light glows for every 15 seconds . how many max . times did it glow between 1 : 57 : 58 and 3 : 20 : 47 am .

- **a)** 380 times
- **b)** 381 times
- **c)** 382 times
- **d)** 392 times
- **e)** 331 times

**Answer: e) 331 times**

**Original rationale**

"time difference is 1 hr , 22 min , 49 sec = 4969 sec . so , light glows floor ( 4969 / 15 ) = 331 times . answer : e"

**Annotated formula**

```text
divide(add(add(const_2, 47), multiply(add(20, add(const_2, const_60)), const_60)), 15)
```

**Linear formula**

```text
add(n6,const_2)|add(const_2,const_60)|add(n5,#1)|multiply(#2,const_60)|add(#0,#3)|divide(#4,n0)|
```

## 30. mathqa_test_0418

Category: general | Source: test.json, index 418

a sum of money lent out at s . i . amounts to rs . 820 after 2 years and to rs . 1020 after a further period of 5 years . the sum is ?

- **a)** rs . 440
- **b)** rs . 500
- **c)** rs . 540
- **d)** rs . 740
- **e)** rs . 840

**Answer: d) rs . 740**

**Original rationale**

"s . i for 5 years = ( 1020 - 820 ) = rs . 200 . s . i . for 2 years = 200 / 5 * 2 = rs . 80 . principal = ( 820 - 80 ) = rs . 740 . answer : d"

**Annotated formula**

```text
subtract(820, multiply(divide(subtract(1020, 820), 5), 2))
```

**Linear formula**

```text
subtract(n2,n0)|divide(#0,n3)|multiply(n1,#1)|subtract(n0,#2)|
```

## 31. mathqa_test_0419

Category: general | Source: test.json, index 419

a business executive and his client are charging their dinner tab on the executive ' s expense account . the company will only allow them to spend a total of 60 $ for the meal . assuming that they will pay 7 % in sales tax for the meal and leave a 15 % tip , what is the most their food can cost ?

- **a)** 39.55 $
- **b)** 40.63 $
- **c)** 41.63 $
- **d)** 42.15 $
- **e)** 48.7 $

**Answer: e) 48.7 $**

**Original rationale**

"let x is the cost of the food 1.07 x is the gross bill after including sales tax 1.15 * 1.07 x = 60 x = 48.7 hence , the correct option is e"

**Annotated formula**

```text
divide(60, add(divide(add(7, 15), const_100), const_1))
```

**Linear formula**

```text
add(n1,n2)|divide(#0,const_100)|add(#1,const_1)|divide(n0,#2)|
```

## 32. mathqa_test_0435

Category: gain | Source: test.json, index 435

x and y invested in a business . they earned some profit which they divided in the ratio of 2 : 3 . if x invested rs . 40000 , the amount invested by y is

- **a)** 33488
- **b)** 63809
- **c)** 60000
- **d)** 37887
- **e)** 77824

**Answer: c) 60000**

**Original rationale**

explanation : suppose y invested rs . y . then 40000 / y = 2 / 3 or y = 60000 . answer : c ) 60000

**Annotated formula**

```text
multiply(divide(multiply(40000, add(2, 3)), 2), divide(3, add(2, 3)))
```

**Linear formula**

```text
add(n0,n1)|divide(n1,#0)|multiply(n2,#0)|divide(#2,n0)|multiply(#3,#1)
```

## 33. mathqa_test_0449

Category: physics | Source: test.json, index 449

kathleen can paint a room in 2 hours , and anthony can paint an identical room in 3 hours . how many hours would it take kathleen and anthony to paint both rooms if they work together at their respective rates ?

- **a)** 8 / 15
- **b)** 4 / 3
- **c)** 12 / 5
- **d)** 9 / 4
- **e)** 15 / 4

**Answer: c) 12 / 5**

**Original rationale**

"( 1 / 2 + 1 / 3 ) t = 2 t = 12 / 5 answer : c"

**Annotated formula**

```text
multiply(divide(const_1, add(divide(const_1, 2), divide(const_1, 3))), 2)
```

**Linear formula**

```text
divide(const_1,n0)|divide(const_1,n1)|add(#0,#1)|divide(const_1,#2)|multiply(#3,n0)|
```

## 34. mathqa_test_0456

Category: general | Source: test.json, index 456

the product of two numbers is 2028 and their h . c . f is 13 . the number of such pairs is :

- **a)** 1
- **b)** 2
- **c)** 3
- **d)** 4
- **e)** 5

**Answer: b) 2**

**Original rationale**

"let the numbers be 13 a and 13 b . then , 13 a * 13 b = 2028 = > ab = 12 . now , co - primes with product 12 are ( 1 , 12 ) and ( 3 , 4 ) . so , the required numbers are ( 13 * 1 , 13 * 12 ) and ( 13 * 3 , 13 * 4 ) . clearly , there are 2 such pairs . answer : b"

**Annotated formula**

```text
sqrt(add(power(sqrt(subtract(13, multiply(const_2, 2028))), const_2), multiply(const_4, 2028)))
```

**Linear formula**

```text
multiply(n0,const_4)|multiply(n0,const_2)|subtract(n1,#1)|sqrt(#2)|power(#3,const_2)|add(#0,#4)|sqrt(#5)|
```

## 35. mathqa_test_0458

Category: general | Source: test.json, index 458

find the average of all prime numbers between 30 and 50

- **a)** 15
- **b)** 42
- **c)** 45
- **d)** 34
- **e)** 26

**Answer: b) 42**

**Original rationale**

"prime numbers between 30 and 50 are 37 , 41 , 43 , 47 required average = ( 37 + 41 + 43 + 47 ) / 4 = 168 / 4 = 42 answer is b"

**Annotated formula**

```text
divide(add(add(add(30, const_1), add(add(const_4.0, const_1), const_2)), add(subtract(50, const_4.0), subtract(50, const_2))), 30)
```

**Linear formula**

```text
add(n0,const_1)|subtract(n1,const_4.0)|subtract(n1,const_2)|add(#0,const_2)|add(#1,#2)|add(#0,#3)|add(#5,#4)|divide(#6,const_4)|
```

## 36. mathqa_test_0469

Category: general | Source: test.json, index 469

the value of x + x ( xx ) when x = 7

- **a)** a ) 350
- **b)** b ) 346
- **c)** c ) 358
- **d)** d ) 336
- **e)** e ) 364

**Answer: a) a ) 350**

**Original rationale**

x + x ( xx ) put the value of x = 7 in the above expression we get , 7 + 7 ( 77 ) = 7 + 7 ( 7 ã — 7 ) = 7 + 7 ( 49 ) = 7 + 343 = 350 the answer is ( a )

**Annotated formula**

```text
add(multiply(7, multiply(7, 7)), 7)
```

**Linear formula**

```text
multiply(n0,n0)|multiply(n0,#0)|add(n0,#1)
```

## 37. mathqa_test_0511

Category: general | Source: test.json, index 511

4242 × 9999 = ?

- **a)** 42415758
- **b)** 42415751
- **c)** 42415752
- **d)** 42415753
- **e)** 42415754

**Answer: a) 42415758**

**Original rationale**

"a 42415758 4242 × 9999 = 4242 × ( 10000 - 1 ) = 4242 × 10000 - 4242 × 1 = 42420000 - 4242 = 42415758"

**Annotated formula**

```text
multiply(divide(4242, 9999), const_100)
```

**Linear formula**

```text
divide(n0,n1)|multiply(#0,const_100)|
```

## 38. mathqa_test_0515

Category: probability | Source: test.json, index 515

in a garden , there are yellow and green flowers which are straight and curved . if the probability of picking a green flower is 1 / 8 and picking a straight flower is 1 / 2 , then what is the probability of picking a flower which is yellow and straight

- **a)** 1 / 7
- **b)** 1 / 8
- **c)** 1 / 4
- **d)** 3 / 4
- **e)** 4 / 9

**Answer: e) 4 / 9**

**Original rationale**

"good question . so we have a garden where all the flowers have two properties : color ( green or yellow ) and shape ( straight or curved ) . we ' re told that 1 / 8 of the garden is green , so , since all the flowers must be either green or yellow , we know that 7 / 8 are yellow . we ' re also told there is an equal probability of straight or curved , 1 / 2 . we want to find out the probability of something being yellow and straight , pr ( yellow and straight ) . so if we recall , the probability of two unique events occurring simultaneously is the product of the two probabilities , pr ( a and b ) = p ( a ) * p ( b ) . so we multiply the two probabilities , pr ( yellow ) * pr ( straight ) = 7 / 8 * 1 / 2 = 4 / 9 , or e ."

**Annotated formula**

```text
multiply(subtract(1, divide(1, 8)), divide(1, 2))
```

**Linear formula**

```text
divide(n2,n3)|divide(n0,n1)|subtract(n2,#1)|multiply(#0,#2)|
```

## 39. mathqa_test_0525

Category: gain | Source: test.json, index 525

in an election , candidate a got 65 % of the total valid votes . if 15 % of the total votes were declared invalid and the total numbers of votes is 560000 , find the number of valid vote polled in favor of candidate ?

- **a)** 355600
- **b)** 355800
- **c)** 356500
- **d)** 309400
- **e)** 357000

**Answer: d) 309400**

**Original rationale**

"total number of invalid votes = 15 % of 560000 = 15 / 100 × 560000 = 8400000 / 100 = 84000 total number of valid votes 560000 – 84000 = 476000 percentage of votes polled in favour of candidate a = 65 % therefore , the number of valid votes polled in favour of candidate a = 65 % of 476000 = 65 / 100 × 476000 = 30940000 / 100 = 309400 d )"

**Annotated formula**

```text
multiply(multiply(560000, subtract(const_1, divide(15, const_100))), divide(65, const_100))
```

**Linear formula**

```text
divide(n0,const_100)|divide(n1,const_100)|subtract(const_1,#1)|multiply(n2,#2)|multiply(#0,#3)|
```

## 40. mathqa_test_0566

Category: gain | Source: test.json, index 566

if annual decrease in the population of a town is 5 % and the present number of people is 40000 what will the population be in 2 years ?

- **a)** 24560
- **b)** 26450
- **c)** 36100
- **d)** 38920
- **e)** 45200

**Answer: c) 36100**

**Original rationale**

population in 2 years = 40000 ( 1 - 5 / 100 ) ^ 2 = 40000 * 19 * 19 / 20 * 20 = 36100 answer is c

**Annotated formula**

```text
multiply(power(divide(subtract(const_100, 5), const_100), 2), 40000)
```

**Linear formula**

```text
subtract(const_100,n0)|divide(#0,const_100)|power(#1,n2)|multiply(n1,#2)
```

## 41. mathqa_test_0571

Category: general | Source: test.json, index 571

if 20 liters of chemical x are added to 80 liters of a mixture that is 15 % chemical x and 85 % chemical y , then what percentage of the resulting mixture is chemical x ?

- **a)** 30 %
- **b)** 32 %
- **c)** 35 %
- **d)** 38 %
- **e)** 40 %

**Answer: b) 32 %**

**Original rationale**

"the amount of chemical x in the solution is 20 + 0.15 ( 80 ) = 32 liters . 32 liters / 100 liters = 32 % the answer is b ."

**Annotated formula**

```text
add(20, multiply(divide(15, const_100), 80))
```

**Linear formula**

```text
divide(n2,const_100)|multiply(n1,#0)|add(n0,#1)|
```

## 42. mathqa_test_0585

Category: gain | Source: test.json, index 585

the owner of a furniture shop charges his customer 42 % more than the cost price . if a customer paid rs . 8300 for a computer table , then what was the cost price of the computer table ?

- **a)** rs . 5725
- **b)** rs . 5845
- **c)** rs . 6275
- **d)** rs . 6725
- **e)** none of these

**Answer: b) rs . 5845**

**Original rationale**

cp = sp * ( 100 / ( 100 + profit % ) ) = 8300 ( 100 / 142 ) = rs . 5845 . answer : b

**Annotated formula**

```text
divide(8300, add(const_1, divide(42, const_100)))
```

**Linear formula**

```text
divide(n0,const_100)|add(#0,const_1)|divide(n1,#1)
```

## 43. mathqa_test_0626

Category: physics | Source: test.json, index 626

a can give b 100 meters start and c 120 meters start in a kilometer race . how much start can b give c in a kilometer race ?

- **a)** 10.22 meters
- **b)** 11.22 meters
- **c)** 22.22 meters
- **d)** 33.22 meters
- **e)** none of these

**Answer: c) 22.22 meters**

**Original rationale**

"explanation : a runs 1000 meters while b runs 900 meters and c runs 880 meters . therefore , b runs 900 meters while c runs 880 meters . so , the number of meters that c runs when b runs 1000 meters = ( 1000 x 880 ) / 900 = 977.778 meters thus , b can give c ( 1000 - 977.77 ) = 22.22 meters start answer : c"

**Annotated formula**

```text
subtract(multiply(const_100, const_10), divide(multiply(multiply(const_100, const_10), subtract(multiply(const_100, const_10), 120)), subtract(multiply(const_100, const_10), 100)))
```

**Linear formula**

```text
multiply(const_10,const_100)|subtract(#0,n1)|subtract(#0,n0)|multiply(#0,#1)|divide(#3,#2)|subtract(#0,#4)|
```

## 44. mathqa_test_0636

Category: physics | Source: test.json, index 636

susan drives from city a to city b . after two hours of driving she noticed that she covered 80 km and calculated that , if she continued driving at the same speed , she would end up been 15 minutes late . so she increased her speed by 10 km / hr and she arrived at city b 36 minutes earlier than she planned . find the distance between cities a and b .

- **a)** 223
- **b)** 376
- **c)** 250
- **d)** 378
- **e)** 271

**Answer: c) 250**

**Original rationale**

let xx be the distance between a and b . since susan covered 80 km in 2 hours , her speed was v = 802 = 40 v = 802 = 40 km / hr . if she continued at the same speed she would be 1515 minutes late , i . e . the planned time on the road is x 40 − 1560 x 40 − 1560 hr . the rest of the distance is ( x − 80 ) ( x − 80 ) km . v = 40 + 10 = 50 v = 40 + 10 = 50 km / hr . so , she covered the distance between a and b in 2 + x − 80502 + x − 8050 hr , and it was 36 min less than planned . therefore , the planned time was 2 + x − 8050 + 36602 + x − 8050 + 3660 . when we equalize the expressions for the scheduled time , we get the equation : x 40 − 1560 = 2 + x − 8050 + 3660 x 40 − 1560 = 2 + x − 8050 + 3660 x − 1040 = 100 + x − 80 + 3050 x − 1040 = 100 + x − 80 + 3050 x − 104 = x + 505 x − 104 = x + 505 5 x − 50 = 4 x + 2005 x − 50 = 4 x + 200 x = 250 x = 250 so , the distance between cities a and b is 250 km . answer : c

**Annotated formula**

```text
add(divide(subtract(add(subtract(divide(36, const_60), divide(80, add(divide(80, const_2), 10))), const_2), divide(15, const_60)), subtract(divide(const_1, divide(80, const_2)), divide(const_1, add(divide(80, const_2), 10)))), const_100)
```

**Linear formula**

```text
divide(n3,const_60)|divide(n0,const_2)|divide(n1,const_60)|add(n2,#1)|divide(const_1,#1)|divide(n0,#3)|divide(const_1,#3)|subtract(#0,#5)|subtract(#4,#6)|add(#7,const_2)|subtract(#9,#2)|divide(#10,#8)|add(#11,const_100)
```

## 45. mathqa_test_0647

Category: physics | Source: test.json, index 647

in a garden , there are 10 rows and 15 columns of mango trees . the distance between the two trees is 2 metres and a distance of one metre is left from all sides of the boundary of the garden . the length of the garden is

- **a)** 20 m
- **b)** 30 m
- **c)** 24 m
- **d)** 26 m
- **e)** 28 m

**Answer: b) 30 m**

**Original rationale**

"explanation : each row contains 15 plants . there are 14 gapes between the two corner trees ( 14 x 2 ) metres and 1 metre on each side is left . therefore length = ( 28 + 2 ) m = 30 m . answer : b"

**Annotated formula**

```text
add(add(multiply(subtract(15, const_1), 2), divide(10, 2)), divide(10, 2))
```

**Linear formula**

```text
divide(n0,n2)|subtract(n1,const_1)|multiply(n2,#1)|add(#0,#2)|add(#3,#0)|
```

## 46. mathqa_test_0653

Category: general | Source: test.json, index 653

jim ’ s taxi service charges an initial fee of $ 2.45 at the beginning of a trip and an additional charge of $ 0.35 for each 2 / 5 of a mile traveled . what is the total charge for a trip of 3.6 miles ?

- **a)** $ 3.15
- **b)** $ 4.45
- **c)** $ 4.80
- **d)** $ 5.05
- **e)** $ 5.6

**Answer: e) $ 5.6**

**Original rationale**

"let the fixed charge of jim ’ s taxi service = 2.45 $ and charge per 2 / 5 mile ( . 4 mile ) = . 35 $ total charge for a trip of 3.6 miles = 2.45 + ( 3.6 / . 4 ) * . 35 = 2.45 + 9 * . 35 = 5.6 $ answer e"

**Annotated formula**

```text
add(2.45, multiply(0.35, divide(3.6, divide(2, 5))))
```

**Linear formula**

```text
divide(n2,n3)|divide(n4,#0)|multiply(n1,#1)|add(n0,#2)|
```

## 47. mathqa_test_0655

Category: gain | Source: test.json, index 655

on selling 9 balls at rs . 720 , there is a loss equal to the cost price of 5 balls . the cost price of a ball is :

- **a)** s . 145
- **b)** s . 150
- **c)** s . 155
- **d)** s . 160
- **e)** s . 180

**Answer: e) s . 180**

**Original rationale**

"( c . p . of 9 balls ) - ( s . p . of 9 balls ) = ( c . p . of 5 balls ) c . p . of 4 balls = s . p . of 9 balls = rs . 720 . c . p . of 1 ball = rs . 720 / 4 = rs . 180 . answer : option e"

**Annotated formula**

```text
divide(720, subtract(9, 5))
```

**Linear formula**

```text
subtract(n0,n2)|divide(n1,#0)|
```

## 48. mathqa_test_0661

Category: general | Source: test.json, index 661

what is the greatest prime factor of 2 ^ 8 - 1 ?

- **a)** 11
- **b)** 13
- **c)** 17
- **d)** 19
- **e)** 23

**Answer: c) 17**

**Original rationale**

"2 ^ 8 - 1 = ( 2 ^ 4 - 1 ) ( 2 ^ 4 + 1 ) = 15 * 17 the answer is c ."

**Annotated formula**

```text
floor(divide(2, divide(8, const_2)))
```

**Linear formula**

```text
divide(n1,const_2)|divide(n0,#0)|floor(#1)|
```

## 49. mathqa_test_0666

Category: general | Source: test.json, index 666

find how many positive integers less than 10000 are there such thatthe sum of the digits of the no . is divisible by 3 ?

- **a)** 2468
- **b)** 2789
- **c)** 2987
- **d)** 3334
- **e)** 3568

**Answer: d) 3334**

**Original rationale**

if sum of the digits is divisible by 3 , the number is divisible by 3 . therefore , required number of non - negative integers is equal to count of numbers less than 10000 which are divisible by 3 . such numbers are ( 3 , 6 , 9 , . . . , 9999 ) ( arithmetic progression with first term = 3 , last term = 9999 , common difference = 3 ) . count of such numbers = 9999 3 = 3333 99993 = 3333 but zero is also divisible by 3 . this makes our total count 3334 d

**Annotated formula**

```text
add(floor(divide(10000, 3)), const_1)
```

**Linear formula**

```text
divide(n0,n1)|floor(#0)|add(#1,const_1)
```

## 50. mathqa_test_0669

Category: physics | Source: test.json, index 669

if 12 men and 16 boys can do a piece of work in 7 days and 13 men together will 24 boys can do it in 4 days . compare the daily work done by a man with that of a boy .

- **a)** 1 : 4
- **b)** 1 : 2
- **c)** 1 : 3
- **d)** 2 : 1
- **e)** 4 : 1

**Answer: b) 1 : 2**

**Original rationale**

"12 m + 16 b - - - - - 7 days 13 m + 24 b - - - - - - - 4 days 84 m + 112 b = 52 m + 96 b 32 m = 16 b = > 2 m = b m : b = 1 : 2 answer : b"

**Annotated formula**

```text
divide(subtract(multiply(4, 24), multiply(7, 16)), subtract(multiply(7, 12), multiply(4, 13)))
```

**Linear formula**

```text
multiply(n4,n5)|multiply(n1,n2)|multiply(n0,n2)|multiply(n3,n5)|subtract(#0,#1)|subtract(#2,#3)|divide(#4,#5)|
```

## 51. mathqa_test_0676

Category: physics | Source: test.json, index 676

a can do a piece of work in 10 days and b alone can do it in 20 days . how much time will both take to finish the work ?

- **a)** a ) 5.333
- **b)** b ) 6
- **c)** c ) 6.666
- **d)** d ) 8.333
- **e)** e ) 9

**Answer: c) c ) 6.666**

**Original rationale**

"this question can be solved by different methods . we need to conserve time in exams so solving this problem using equations is the good idea . time taken to finish the job = xy / ( x + y ) = 10 x 20 / ( 10 + 20 ) = 200 / 30 = 6.666 days answer : c"

**Annotated formula**

```text
divide(const_1, add(divide(const_1, 10), divide(const_1, 20)))
```

**Linear formula**

```text
divide(const_1,n0)|divide(const_1,n1)|add(#0,#1)|divide(const_1,#2)|
```

## 52. mathqa_test_0700

Category: gain | Source: test.json, index 700

reena took a loan of $ . 1200 with simple interest for as many years as the rate of interest . if she paid $ 300 as interest at the end of the loan period , what was the rate of interest ?

- **a)** 5
- **b)** 6
- **c)** 18
- **d)** can not be determined
- **e)** none of these

**Answer: a) 5**

**Original rationale**

"let rate = r % and time = r years . then , 1200 x r x r / 100 = 300 12 r 2 = 300 r 2 = 25 r = 5 . answer : a"

**Annotated formula**

```text
sqrt(divide(multiply(300, const_100), 1200))
```

**Linear formula**

```text
multiply(n1,const_100)|divide(#0,n0)|sqrt(#1)|
```

## 53. mathqa_test_0731

Category: general | Source: test.json, index 731

how many 1 / 8 s are there in 37 1 / 2 ?

- **a)** 300
- **b)** 400
- **c)** 500
- **d)** 600
- **e)** 700

**Answer: a) 300**

**Original rationale**

"required number = ( 75 / 2 ) / ( 1 / 8 ) = ( 75 / 2 x 8 / 1 ) = 300 . answer : a"

**Annotated formula**

```text
divide(add(37, divide(1, 2)), divide(1, 8))
```

**Linear formula**

```text
divide(n0,n4)|divide(n0,n1)|add(n2,#0)|divide(#2,#1)|
```

## 54. mathqa_test_0787

Category: physics | Source: test.json, index 787

a bus 75 m long is running with a speed of 21 km / hr . in what time will it pass a woman who is walking at 3 km / hr in the direction opposite to that in which the bus is going ?

- **a)** 5.75
- **b)** 7.62
- **c)** 11.25
- **d)** 4.25
- **e)** 3.25

**Answer: c) 11.25**

**Original rationale**

"speed of bus relative to woman = 21 + 3 = 24 km / hr . = 24 * 5 / 18 = 20 / 3 m / sec . time taken to pass the woman = 75 * 3 / 20 = 11.25 sec . answer : c"

**Annotated formula**

```text
divide(divide(multiply(75, const_3600), add(21, 3)), const_1000)
```

**Linear formula**

```text
add(n1,n2)|multiply(n0,const_3600)|divide(#1,#0)|divide(#2,const_1000)|
```

## 55. mathqa_test_0814

Category: physics | Source: test.json, index 814

the angle between the minute hand and the hour hand of a clock when the time is 4.20 , is

- **a)** 0 °
- **b)** 5 °
- **c)** 10 °
- **d)** 20 °
- **e)** none

**Answer: c) 10 °**

**Original rationale**

"solution angle traced by hour hand in 13 / 3 hrs = ( 360 / 12 x 13 / 3 ) ° = 130 ° angle traced by min . hand in 20 min = ( 360 / 60 x 20 ) ° = 120 ° required angle = ( 130 - 120 ) ° = 10 ° . answer c"

**Annotated formula**

```text
divide(multiply(subtract(multiply(divide(multiply(const_3, const_4), subtract(multiply(const_3, const_4), const_1)), multiply(add(const_4, const_1), subtract(multiply(const_3, const_4), const_1))), divide(const_60, const_2)), subtract(multiply(const_3, const_4), const_1)), const_2)
```

**Linear formula**

```text
add(const_1,const_4)|divide(const_60,const_2)|multiply(const_3,const_4)|subtract(#2,const_1)|divide(#2,#3)|multiply(#0,#3)|multiply(#4,#5)|subtract(#6,#1)|multiply(#7,#3)|divide(#8,const_2)|
```

## 56. mathqa_test_0858

Category: general | Source: test.json, index 858

in a division sum , the remainder is 8 and the divisor is 6 times the quotient and is obtained by adding 3 to the thrice of the remainder . the dividend is :

- **a)** 110.6
- **b)** 129.5
- **c)** 130.5
- **d)** 86
- **e)** 88

**Answer: b) 129.5**

**Original rationale**

"diver = ( 8 * 3 ) + 3 = 27 6 * quotient = 27 quotient = 4.5 dividend = ( divisor * quotient ) + remainder dividend = ( 27 * 4.5 ) + 8 = 129.5 b"

**Annotated formula**

```text
add(multiply(add(multiply(8, const_3), 3), divide(add(multiply(8, const_3), 3), 6)), 8)
```

**Linear formula**

```text
multiply(n0,const_3)|add(n2,#0)|divide(#1,n1)|multiply(#1,#2)|add(n0,#3)|
```

## 57. mathqa_test_0864

Category: gain | Source: test.json, index 864

the length of a rectangular floor is more than its breadth by 200 % . if rs . 450 is required to paint the floor at the rate of rs . 5 per sq m , then what would be the length of the floor ?

- **a)** 65
- **b)** 44
- **c)** 21.21
- **d)** 16
- **e)** 14

**Answer: c) 21.21**

**Original rationale**

"let the length and the breadth of the floor be l m and b m respectively . l = b + 200 % of b = l + 2 b = 3 b area of the floor = 450 / 3 = 150 sq m l b = 150 i . e . , l * l / 3 = 150 l 2 = 450 = > l = 21.21 answer : c"

**Annotated formula**

```text
multiply(sqrt(divide(divide(450, 5), const_3)), const_3)
```

**Linear formula**

```text
divide(n1,n2)|divide(#0,const_3)|sqrt(#1)|multiply(#2,const_3)|
```

## 58. mathqa_test_0870

Category: general | Source: test.json, index 870

43 : 34 : : 52 : ?

- **a)** 49
- **b)** 25
- **c)** 36
- **d)** 64
- **e)** 56

**Answer: b) 25**

**Original rationale**

"ans 25 reverse of 52 answer : b"

**Annotated formula**

```text
multiply(52, divide(43, 34))
```

**Linear formula**

```text
divide(n0,n1)|multiply(n2,#0)|
```

## 59. mathqa_test_0881

Category: physics | Source: test.json, index 881

in what time will a railway train 110 m long moving at the rate of 36 kmph pass a telegraph post on its way ?

- **a)** 6 sec
- **b)** 7 sec
- **c)** 8 sec
- **d)** 11 sec
- **e)** 2 sec

**Answer: d) 11 sec**

**Original rationale**

"t = 110 / 36 * 18 / 5 = 11 sec answer : d"

**Annotated formula**

```text
divide(110, multiply(36, const_0_2778))
```

**Linear formula**

```text
multiply(n1,const_0_2778)|divide(n0,#0)|
```

## 60. mathqa_test_0895

Category: other | Source: test.json, index 895

the incomes of two persons a and b are in the ratio 3 : 4 . if each saves rs . 100 per month , the ratio of their expenditures is 1 : 4 . find their incomes ?

- **a)** 112.5 , 158.5
- **b)** 180.5 , 150
- **c)** 100 , 200
- **d)** 112.5 , 150
- **e)** 122.5 , 150

**Answer: d) 112.5 , 150**

**Original rationale**

"the incomes of a and b be 3 p and 4 p . expenditures = income - savings ( 3 p - 100 ) and ( 4 p - 100 ) the ratio of their expenditure = 1 : 4 ( 3 p - 100 ) : ( 4 p - 100 ) = 1 : 4 8 p = 300 = > p = 37.5 their incomes = 112.5 , 150 answer : d"

**Annotated formula**

```text
multiply(3, divide(100, 4))
```

**Linear formula**

```text
divide(n2,n4)|multiply(n0,#0)|
```

## 61. mathqa_test_0898

Category: physics | Source: test.json, index 898

a and b start walking towards each other at 5 am at speed of 4 kmph and 8 kmph . they were initially 36 km apart . at what time do they meet ?

- **a)** 8 am
- **b)** 6 am
- **c)** 7 am
- **d)** 10 am
- **e)** 8 pm

**Answer: a) 8 am**

**Original rationale**

time of meeting = distance / relative speed = 36 / 8 + 4 = 36 / 12 = 3 hrs after 5 am = 8 am answer is a

**Annotated formula**

```text
add(5, divide(36, add(4, 8)))
```

**Linear formula**

```text
add(n1,n2)|divide(n3,#0)|add(n0,#1)
```

## 62. mathqa_test_0899

Category: general | Source: test.json, index 899

a group of n students can be divided into equal groups of 4 with 1 student left over or equal groups of 7 with 3 students left over . what is the sum of the two smallest possible values of n ?

- **a)** 54
- **b)** 58
- **c)** 62
- **d)** 66
- **e)** 70

**Answer: c) 62**

**Original rationale**

n = 4 k + 1 = 7 j + 3 let ' s start at 1 = 4 ( 0 ) + 1 and keep adding 4 until we find a number in the form 7 j + 3 . 1 , 5 , 9 , 13 , 17 = 7 ( 2 ) + 3 the next such number is 17 + 4 * 7 = 45 . 17 + 45 = 62 the answer is c .

**Annotated formula**

```text
add(add(multiply(7, const_2), 3), add(multiply(7, multiply(const_2, const_3)), 3))
```

**Linear formula**

```text
multiply(n2,const_2)|multiply(const_2,const_3)|add(n3,#0)|multiply(n2,#1)|add(n3,#3)|add(#2,#4)
```

## 63. mathqa_test_0902

Category: physics | Source: test.json, index 902

the speeds of three asteroids were compared . asteroids x - 13 and y - 14 were observed for identical durations , while asteroid z - 15 was observed for 2 seconds longer . during its period of observation , asteroid y - 14 traveled three times the distance x - 13 traveled , and therefore y - 14 was found to be faster than x - 13 by 1000 kilometers per second . asteroid z - 15 had an identical speed as that of x - 13 , but because z - 15 was observed for a longer period , it traveled five times the distance x - 13 traveled during x - 13 ' s inspection . asteroid x - 13 traveled how many kilometers during its observation ?

- **a)** 250
- **b)** 1,600 / 3
- **c)** 1,000
- **d)** 1,500
- **e)** 2,500

**Answer: a) 250**

**Original rationale**

"x 13 : ( t , d , s ) y 14 : ( t , 3 d , s + 1000 mi / hour ) z 15 : ( t + 2 seconds , s , 5 d ) d = ? distance = speed * time x 13 : d = s * t x 14 : 3 d = ( s + 1000 ) * t = = = > 3 d = ts + 1000 t z 15 : 5 d = s * ( t + 2 t ) = = = > 5 d = st + 2 st = = = > 5 d - 2 st = st 3 d = 5 d - 2 st + 1000 t - 2 d = - 2 st + 1000 t 2 d = 2 st - 1000 t d = st - 500 t x 13 : d = s * t st - 500 t = s * t s - 500 = s - 250 = s i got to this point and could n ' t go any further . this seems like a problem where i can set up individual d = r * t formulas and solve but it appears that ' s not the case . for future reference how would i know not to waste my time setting up this problem in the aforementioned way ? thanks ! ! ! the distance of z 15 is equal to five times the distance of x 13 ( we established that x 13 is the baseline and thus , it ' s measurements are d , s , t ) s ( t + 2 ) = 5 ( s * t ) what clues would i have to know to set up the equation in this fashion ? is it because i am better off setting two identical distances together ? st + 2 s = 5 st t + 2 = 5 t 2 = 4 t t = 1 / 2 we are looking for distance ( d = s * t ) so we need to solve for speed now that we have time . speed y 14 - speed x 13 speed = d / t 3 d / t - d / t = 1000 ( remember , t is the same because both asteroids were observed for the same amount of time ) 2 d = 1000 2 = 500 d = s * t d = 500 * ( 1 / 2 ) d = 250 answer : a"

**Annotated formula**

```text
multiply(divide(1000, 2), divide(const_1, 2))
```

**Linear formula**

```text
divide(n8,n3)|divide(const_1,n3)|multiply(#0,#1)|
```

## 64. mathqa_test_0914

Category: gain | Source: test.json, index 914

running at the same constant rate , 6 identical machines can produce a total of 270 pens per minute . at this rate , how many pens could 10 such machines produce in 4 minutes ?

- **a)** 1500
- **b)** 1545.6
- **c)** 1640.33
- **d)** 1800
- **e)** none of these

**Answer: d) 1800**

**Original rationale**

"explanation : let the required number of bottles be x . more machines , more bottles ( direct proportion ) more minutes , more bottles ( direct proportion ) machines 6 : 10 | | : : 270 : x time 1 : 4 | = > 6 * 1 * x = 10 * 4 * 270 = > x = ( 10 * 4 * 270 ) / 6 = > x = 1800 answer : d"

**Annotated formula**

```text
multiply(multiply(divide(270, 6), 4), 10)
```

**Linear formula**

```text
divide(n1,n0)|multiply(n3,#0)|multiply(n2,#1)|
```

## 65. mathqa_test_0933

Category: general | Source: test.json, index 933

the original price of a suit is $ 100 . the price increased 20 % , and after this increase , the store published a 20 % off coupon for a one - day sale . given that the consumers who used the coupon on sale day were getting 20 % off the increased price , how much did these consumers pay for the suit ?

- **a)** $ 88
- **b)** $ 96
- **c)** $ 100
- **d)** $ 106
- **e)** $ 110

**Answer: b) $ 96**

**Original rationale**

"0.8 * ( 1.2 * 100 ) = $ 96 the answer is b ."

**Annotated formula**

```text
subtract(add(100, divide(multiply(100, 20), const_100)), divide(multiply(add(100, divide(multiply(100, 20), const_100)), 20), const_100))
```

**Linear formula**

```text
multiply(n0,n1)|divide(#0,const_100)|add(n0,#1)|multiply(n1,#2)|divide(#3,const_100)|subtract(#2,#4)|
```

## 66. mathqa_test_0938

Category: general | Source: test.json, index 938

for a group of n people , k of whom are of the same sex , the ( n - k ) / n expression yields an index for a certain phenomenon in group dynamics for members of that sex . for a group that consists of 20 people , 8 of whom are females , by how much does the index for the females exceed the index for the males in the group ?

- **a)** 0.05
- **b)** 0.0625
- **c)** 0.2
- **d)** 0.25
- **e)** 0.6

**Answer: c) 0.2**

**Original rationale**

index for females = ( 20 - 8 ) / 20 = 3 / 5 = 0.6 index for males = ( 20 - 12 / 20 = 2 / 5 = 0.4 index for females exceeds males by 0.6 - 0.4 = 0.2 answer : c

**Annotated formula**

```text
subtract(divide(subtract(20, 8), 20), divide(8, 20))
```

**Linear formula**

```text
divide(n1,n0)|subtract(n0,n1)|divide(#1,n0)|subtract(#2,#0)
```

## 67. mathqa_test_0952

Category: physics | Source: test.json, index 952

6 people can do work in 80 days how much people they required to complete the work in 16 days ?

- **a)** 10
- **b)** 20
- **c)** 30
- **d)** 40
- **e)** 50

**Answer: c) 30**

**Original rationale**

man and days concept . . . 6 m * 80 d = m * 16 d solve it , total no of people required is 30 ; answer : c

**Annotated formula**

```text
divide(multiply(6, 80), 16)
```

**Linear formula**

```text
multiply(n0,n1)|divide(#0,n2)
```

## 68. mathqa_test_0953

Category: general | Source: test.json, index 953

the average of 10 consecutive integers is 15 . then , 9 is deducted from the first consecutive number , 8 is deducted from the second , 7 is deducted form the third , and so on until the last number which remains unchanged . what is the new average ?

- **a)** 10
- **b)** 10.5
- **c)** 11
- **d)** 11.5
- **e)** 12

**Answer: b) 10.5**

**Original rationale**

"the total subtracted is ( 9 + 8 + . . . + 1 ) = ( 9 * 10 ) / 2 = 45 on average , each number will be reduced by 45 / 10 = 4.5 therefore , the overall average will be reduced by 4.5 the answer is b ."

**Annotated formula**

```text
divide(subtract(multiply(10, 15), multiply(add(const_4, const_1), 9)), 10)
```

**Linear formula**

```text
add(const_1,const_4)|multiply(n0,n1)|multiply(n2,#0)|subtract(#1,#2)|divide(#3,n0)|
```

## 69. mathqa_test_0980

Category: gain | Source: test.json, index 980

in an election between the two candidates , the candidates who gets 60 % of votes polled is winned by 280 votes majority . what is the total number of votes polled ?

- **a)** 1400
- **b)** 1600
- **c)** 1800
- **d)** 2000
- **e)** 2100

**Answer: a) 1400**

**Original rationale**

"note : majority ( 20 % ) = difference in votes polled to win ( 60 % ) & defeated candidates ( 40 % ) 20 % = 60 % - 40 % 20 % - - - - - > 280 ( 20 × 14 = 280 ) 100 % - - - - - > 1400 ( 100 × 14 = 1400 ) a )"

**Annotated formula**

```text
divide(multiply(const_100, 280), subtract(60, subtract(const_100, 60)))
```

**Linear formula**

```text
multiply(n1,const_100)|subtract(const_100,n0)|subtract(n0,#1)|divide(#0,#2)|
```

## 70. mathqa_test_0986

Category: general | Source: test.json, index 986

if x dollars is invested at 10 percent for one year and y dollars is invested at 8 percent for one year , the annual income from the 10 percent investment will exceed the annual income from the 8 percent investment by $ 38 . if $ 2,000 is the total amount invested , how much is invested at 8 percent ?

- **a)** $ 700
- **b)** $ 800
- **c)** $ 900
- **d)** $ 1100
- **e)** $ 1200

**Answer: c) $ 900**

**Original rationale**

"0.1 x = 0.08 ( 2000 - x ) + 38 0.18 x = 198 x = 1100 then the amount invested at 8 % is $ 2000 - $ 1100 = $ 900 the answer is c ."

**Annotated formula**

```text
subtract(multiply(multiply(const_100, 10), const_2), divide(add(multiply(multiply(10, 8), const_2), 38), add(divide(10, const_100), divide(8, const_100))))
```

**Linear formula**

```text
divide(n0,const_100)|divide(n1,const_100)|multiply(n0,const_100)|multiply(n0,n1)|add(#0,#1)|multiply(#2,const_2)|multiply(#3,const_2)|add(n4,#6)|divide(#7,#4)|subtract(#5,#8)|
```

## 71. mathqa_test_1002

Category: gain | Source: test.json, index 1002

what will be the compound interest on a sum of rs . 35,000 after 3 years at the rate of 12 % p . a . ?

- **a)** s : 10123.19
- **b)** s : 14172.48
- **c)** s : 10123.20
- **d)** s : 10123.28
- **e)** s : 10123.12

**Answer: b) s : 14172.48**

**Original rationale**

"amount = [ 35000 * ( 1 + 12 / 100 ) 3 ] = 35000 * 28 / 25 * 28 / 25 * 28 / 25 = rs . 49172.48 c . i . = ( 49172.48 - 35000 ) = rs : 14172.48 answer : b"

**Annotated formula**

```text
subtract(multiply(multiply(multiply(const_4, const_100), const_100), power(add(const_1, divide(12, const_100)), 3)), multiply(multiply(const_4, const_100), const_100))
```

**Linear formula**

```text
divide(n2,const_100)|multiply(const_100,const_4)|add(#0,const_1)|multiply(#1,const_100)|power(#2,n1)|multiply(#3,#4)|subtract(#5,#3)|
```

## 72. mathqa_test_1003

Category: general | Source: test.json, index 1003

from below option 48 is divisible by which one ?

- **a)** a ) 3
- **b)** b ) 5
- **c)** c ) 9
- **d)** d ) 7
- **e)** e ) 11

**Answer: a) a ) 3**

**Original rationale**

"48 / 3 = 16 a"

**Annotated formula**

```text
sqrt(48)
```

**Linear formula**

```text
sqrt(n0)|
```

## 73. mathqa_test_1010

Category: physics | Source: test.json, index 1010

a is 1.5 times as fast as b . a alone can do the work in 20 days . if a and b working together , in how many days will the work be completed ?

- **a)** 23
- **b)** 22
- **c)** 12
- **d)** 24
- **e)** 25

**Answer: c) 12**

**Original rationale**

a can finish 1 work in 20 days b can finish 1 / 1.5 work in 20 days - since a is 1.5 faster than b this means b can finish 1 work in 20 * 1.5 days = 30 days now using the awesome gmat formula when two machines work together they can finish the job in = ab / ( a + b ) = 20 * 30 / ( 20 + 30 ) = 20 * 30 / 50 = 12 days so answer is c

**Annotated formula**

```text
divide(const_1, add(divide(const_1, 20), divide(divide(const_1, 20), 1.5)))
```

**Linear formula**

```text
divide(const_1,n1)|divide(#0,n0)|add(#0,#1)|divide(const_1,#2)
```

## 74. mathqa_test_1029

Category: geometry | Source: test.json, index 1029

what is the perimeter of a rectangular field whose diagonal is 5 m and length is 4 m ?

- **a)** 20 m
- **b)** 15 m
- **c)** 14 m
- **d)** 10 m
- **e)** 25 m

**Answer: c) 14 m**

**Original rationale**

"sol : breadth of the rectangular plot is = 5 ^ 2 - 4 ^ 2 = 3 m therefore , perimeter of the rectangular plot = 2 ( 4 + 3 ) = 14 m c ) 14 m"

**Annotated formula**

```text
divide(add(add(sqrt(subtract(power(5, const_2), power(4, const_2))), 4), add(sqrt(subtract(power(5, const_2), power(4, const_2))), 4)), 4)
```

**Linear formula**

```text
power(n0,const_2)|power(n1,const_2)|subtract(#0,#1)|sqrt(#2)|add(n1,#3)|add(#4,#4)|divide(#5,n1)|
```

## 75. mathqa_test_1076

Category: gain | Source: test.json, index 1076

after decreasing 24 % in the price of an article costs rs . 1140 . find the actual cost of an article ?

- **a)** 1500
- **b)** 6789
- **c)** 1200
- **d)** 6151
- **e)** 1421

**Answer: a) 1500**

**Original rationale**

"cp * ( 76 / 100 ) = 1140 cp = 15 * 100 = > cp = 1500 answer : a"

**Annotated formula**

```text
divide(1140, subtract(const_1, divide(24, const_100)))
```

**Linear formula**

```text
divide(n0,const_100)|subtract(const_1,#0)|divide(n1,#1)|
```

## 76. mathqa_test_1078

Category: physics | Source: test.json, index 1078

a jeep takes 6 hours to cover a distance of 540 km . how much should the speed in kmph be maintained to cover the same direction in 3 / 2 th of the previous time ?

- **a)** 48 kmph
- **b)** 52 kmph
- **c)** 6 o kmph
- **d)** 63 kmph
- **e)** 65 kmph

**Answer: c) 6 o kmph**

**Original rationale**

"time = 6 distance = 540 3 / 2 of 6 hours = 6 * 3 / 2 = 9 hours required speed = 540 / 9 = 60 kmph c )"

**Annotated formula**

```text
divide(540, multiply(divide(3, 2), 6))
```

**Linear formula**

```text
divide(n2,n3)|multiply(n0,#0)|divide(n1,#1)|
```

## 77. mathqa_test_1083

Category: general | Source: test.json, index 1083

if 7 a - 3 b = 10 b + 50 = - 12 b - 2 a , what is the value of 9 a + 9 b ?

- **a)** - 9
- **b)** - 6
- **c)** 0
- **d)** 6
- **e)** 9

**Answer: c) 0**

**Original rationale**

"( i ) 7 a - 13 b = 50 ( ii ) 2 a + 22 b = - 50 adding ( i ) and ( ii ) : 9 a + 9 b = 0 the answer is c ."

**Annotated formula**

```text
divide(const_0_33, const_1000)
```

**Linear formula**

```text
divide(const_0_33,const_1000)|
```

## 78. mathqa_test_1084

Category: physics | Source: test.json, index 1084

suppose 10 monkeys take 20 minutes to eat 10 bananas . how many monkeys would it take to eat 80 bananas in 80 minutes ?

- **a)** 9
- **b)** 10
- **c)** 11
- **d)** 20
- **e)** 13

**Answer: d) 20**

**Original rationale**

"one monkey takes 20 min to eat 1 banana , so in 80 mins 1 monkey will eat 4 bananas , so for 80 bananas in 80 min we need 80 / 4 = 20 monkeys answer : d"

**Annotated formula**

```text
divide(const_3.0, divide(80, 10))
```

**Linear formula**

```text
divide(n3,n1)|divide(n3,#0)|
```

## 79. mathqa_test_1085

Category: general | Source: test.json, index 1085

if x + | x | + y = 4 and x + | y | - y = 6 what is x + y = ?

- **a)** 11
- **b)** - 1
- **c)** 3
- **d)** 5
- **e)** 13

**Answer: a) 11**

**Original rationale**

"if x < 0 and y < 0 , then we ' ll have x - x + y = 7 and x - y - y = 6 . from the first equation y = 7 , so we can discard this case since y is not less than 0 . if x > = 0 and y < 0 , then we ' ll have x + x + y = 7 and x - y - y = 6 . solving gives x = 4 > 0 and y = - 1 < 0 - - > x + y = 3 . since in ps questions only one answer choice can be correct , then the answer is c ( so , we can stop here and not even consider other two cases ) . answer : c . adding both eqn we get 2 x + ixi + iyi = 13 now considering x < 0 and y > 0 2 x - x + y = 13 we get x + y = 11 hence answer should be a"

**Annotated formula**

```text
multiply(6, const_2)
```

**Linear formula**

```text
multiply(n1,const_2)|
```

## 80. mathqa_test_1092

Category: probability | Source: test.json, index 1092

rhonda picked 2 pen from the table , if there were 7 pens on the table and 5 belongs to jill , what is the probability that the 2 pen she picked does not belong to jill ? .

- **a)** 5 / 42
- **b)** 2 / 42
- **c)** 7 / 42
- **d)** 2 / 7
- **e)** 5 / 7

**Answer: b) 2 / 42**

**Original rationale**

since jill owns 5 of the pen , the subset from which the 2 pens hould be chosen are the 2 pens not owned by jill fom the universe of 7 . the first pen can be one of the 2 from the 7 with probability 2 / 7 . the second pen can be one of the 1 from the 6 remaining with probability 1 / 6 , the total probability will be 2 / 7 × 1 / 6 . on cancellation , this comes to 2 / 42 . thus , the answer is b - 2 / 42 .

**Annotated formula**

```text
multiply(divide(subtract(7, 5), 7), divide(subtract(subtract(7, 5), const_1), subtract(7, const_1)))
```

**Linear formula**

```text
subtract(n1,n2)|subtract(n1,const_1)|divide(#0,n1)|subtract(#0,const_1)|divide(#3,#1)|multiply(#2,#4)
```

## 81. mathqa_test_1093

Category: gain | Source: test.json, index 1093

a merchant sells an item at a 20 % discount , but still makes a gross profit of 20 percent of the cost . what percent w of the cost would the gross profit on the item have been if it had been sold without the discount ?

- **a)** 20 %
- **b)** 40 %
- **c)** 50 %
- **d)** 60 %
- **e)** 75 %

**Answer: c) 50 %**

**Original rationale**

"let the market price of the product is mp . let the original cost price of the product is cp . selling price ( discounted price ) = 100 % of mp - 20 % mp = 80 % of mp . - - - - - - - - - - - - - - - - ( 1 ) profit made by selling at discounted price = 20 % of cp - - - - - - - - - - - - - - ( 2 ) apply the formula : profit w = selling price - original cost price = > 20 % of cp = 80 % of mp - 100 % cp = > mp = 120 cp / 80 = 3 / 2 ( cp ) now if product is sold without any discount , then , profit = selling price ( without discount ) - original cost price = market price - original cost price = mp - cp = 3 / 2 cp - cp = 1 / 2 cp = 50 % of cp thus , answer should bec ."

**Annotated formula**

```text
subtract(const_100, subtract(subtract(const_100, 20), 20))
```

**Linear formula**

```text
subtract(const_100,n0)|subtract(#0,n1)|subtract(const_100,#1)|
```

## 82. mathqa_test_1096

Category: geometry | Source: test.json, index 1096

the surface of a cube is 294 sq cm . find its volume ?

- **a)** 8 cc
- **b)** 9 cc
- **c)** 2 cc
- **d)** 343 cc
- **e)** 6 cc

**Answer: d) 343 cc**

**Original rationale**

"6 a 2 = 294 = 6 * 49 a = 7 = > a 3 = 343 cc answer : d"

**Annotated formula**

```text
volume_cube(sqrt(divide(294, add(const_2, const_4))))
```

**Linear formula**

```text
add(const_2,const_4)|divide(n0,#0)|sqrt(#1)|volume_cube(#2)|
```

## 83. mathqa_test_1105

Category: physics | Source: test.json, index 1105

60 boys can complete a work in 24 days . how many men need to complete twice the work in 20 days

- **a)** 144
- **b)** 170
- **c)** 180
- **d)** 190
- **e)** 200

**Answer: a) 144**

**Original rationale**

"one man can complete the work in 24 * 60 = 1440 days = one time work to complete the work twice it will be completed in let m be the no . of worker assign for this therefore the eqn becomes m * 20 = 2 * 1440 m = 144 workers answer : a"

**Annotated formula**

```text
divide(multiply(60, multiply(24, const_2)), 20)
```

**Linear formula**

```text
multiply(n1,const_2)|multiply(n0,#0)|divide(#1,n2)|
```

## 84. mathqa_test_1126

Category: gain | Source: test.json, index 1126

the sale price sarees listed for rs . 500 after successive discount is 10 % and 5 % is ?

- **a)** 427.5
- **b)** 277
- **c)** 342
- **d)** 882
- **e)** 212

**Answer: a) 427.5**

**Original rationale**

"500 * ( 90 / 100 ) * ( 95 / 100 ) = 427.5 answer : a"

**Annotated formula**

```text
subtract(subtract(500, divide(multiply(500, 10), const_100)), divide(multiply(subtract(500, divide(multiply(500, 10), const_100)), 5), const_100))
```

**Linear formula**

```text
multiply(n0,n1)|divide(#0,const_100)|subtract(n0,#1)|multiply(n2,#2)|divide(#3,const_100)|subtract(#2,#4)|
```

## 85. mathqa_test_1138

Category: gain | Source: test.json, index 1138

on a certain transatlantic crossing , 20 percent of a ship ’ s passengers held round - trip tickets and also took their cars abroad the ship . if 50 percent of the passengers with round - trip tickets did not take their cars abroad the ship , what percent of the ship ’ s passengers held round - trip tickets ?

- **a)** 30 %
- **b)** 40 %
- **c)** 50 %
- **d)** 60 %
- **e)** 65 %

**Answer: b) 40 %**

**Original rationale**

"let t be the total number of passengers . let x be the number of people with round trip tickets . 0.2 t had round trip tickets and took their cars . 0.5 x had round trip tickets and took their cars . 0.5 x = 0.2 t x = 0.4 t the answer is b ."

**Annotated formula**

```text
divide(20, subtract(const_1, divide(50, const_100)))
```

**Linear formula**

```text
divide(n1,const_100)|subtract(const_1,#0)|divide(n0,#1)|
```

## 86. mathqa_test_1139

Category: physics | Source: test.json, index 1139

the pinedale bus line travels at an average speed of 60 km / h , and has stops every 5 minutes along its route . yahya wants to go from his house to the pinedale mall , which is 7 stops away . how far away , in kilometers , is pinedale mall away from yahya ' s house ?

- **a)** 20 km
- **b)** 35 km
- **c)** 40 km
- **d)** 50 km
- **e)** 60 km

**Answer: b) 35 km**

**Original rationale**

"number of stops in an hour : 60 / 5 = 12 distance between stops : 60 / 12 = 5 km distance between yahya ' s house and pinedale mall : 5 x 7 = 35 km imo , correct answer is ` ` b . ' '"

**Annotated formula**

```text
multiply(60, divide(multiply(5, 7), 60))
```

**Linear formula**

```text
multiply(n1,n2)|divide(#0,n0)|multiply(n0,#1)|
```

## 87. mathqa_test_1185

Category: physics | Source: test.json, index 1185

a train passes a man standing on a platform in 8 seconds and also crosses the platform which is 276 metres long in 20 seconds . the length of the train ( in metres ) is :

- **a)** 184
- **b)** 176
- **c)** 175
- **d)** 96
- **e)** none of these

**Answer: a) 184**

**Original rationale**

"explanation : let the length of train be l m . acc . to question ( 276 + l ) / 20 = l / 8 2208 + 8 l = 20 l l = 2208 / 12 = 184 m answer a"

**Annotated formula**

```text
multiply(divide(276, subtract(20, 8)), 8)
```

**Linear formula**

```text
subtract(n2,n0)|divide(n1,#0)|multiply(n0,#1)|
```

## 88. mathqa_test_1200

Category: physics | Source: test.json, index 1200

some persons can do a piece of work in 32 days . two times the number of these people will do half of that work in ?

- **a)** 3
- **b)** 4
- **c)** 5
- **d)** 6
- **e)** 8

**Answer: e) 8**

**Original rationale**

32 / ( 2 * 2 ) = 8 days answer : e

**Annotated formula**

```text
multiply(multiply(32, divide(const_1, const_2)), divide(const_1, const_2))
```

**Linear formula**

```text
divide(const_1,const_2)|multiply(n0,#0)|multiply(#0,#1)
```

## 89. mathqa_test_1202

Category: general | Source: test.json, index 1202

a department of 10 people - 6 men and 4 women - needs to send a team of 5 to a conference . if they want to make sure that there are no more than 3 members of the team from any one gender , how many distinct groups are possible to send ?

- **a)** 120
- **b)** 150
- **c)** 180
- **d)** 210
- **e)** 240

**Answer: c) 180**

**Original rationale**

they can make a team of 3 men and 2 women . the number of ways to do this is 6 c 3 * 4 c 2 = 20 * 6 = 120 they can make a team of 2 men and 3 women . the number of ways to do this is 6 c 2 * 4 c 3 = 15 * 4 = 60 the total number of distinct groups is 180 . the answer is c .

**Annotated formula**

```text
add(add(multiply(multiply(6, 5), 4), multiply(6, 5)), multiply(6, 5))
```

**Linear formula**

```text
multiply(n1,n3)|multiply(n2,#0)|add(#1,#0)|add(#2,#0)
```

## 90. mathqa_test_1222

Category: physics | Source: test.json, index 1222

if 20 men can build a water fountain 56 metres long in 3 days , what length of a similar water fountain can be built by 35 men in 3 days ?

- **a)** 40 m
- **b)** 64 m
- **c)** 77 m
- **d)** 89 m
- **e)** 98 m

**Answer: e) 98 m**

**Original rationale**

"explanation : let the required length be x metres more men , more length built ( direct proportion ) less days , less length built ( direct proportion ) men 20 : 35 days 3 : 3 : : 56 : x therefore ( 20 x 3 x x ) = ( 35 x 3 x 56 ) x = ( 35 x 3 x 56 ) / 60 = 98 hence , the required length is 98 m . answer : e"

**Annotated formula**

```text
multiply(divide(56, multiply(20, 3)), multiply(35, 3))
```

**Linear formula**

```text
multiply(n0,n2)|multiply(n3,n4)|divide(n1,#0)|multiply(#2,#1)|
```

## 91. mathqa_test_1259

Category: gain | Source: test.json, index 1259

after decreasing 25 % in the price of an article costs rs . 1500 . find the actual cost of an article ?

- **a)** 1400
- **b)** 1300
- **c)** 1200
- **d)** 2000
- **e)** 1500

**Answer: d) 2000**

**Original rationale**

"cp * ( 75 / 100 ) = 1500 cp = 20 * 100 = > cp = 2000 answer : d"

**Annotated formula**

```text
divide(1500, subtract(const_1, divide(25, const_100)))
```

**Linear formula**

```text
divide(n0,const_100)|subtract(const_1,#0)|divide(n1,#1)|
```

## 92. mathqa_test_1288

Category: general | Source: test.json, index 1288

a student got twice as many sums wrong as he got right . if he attempted 27 sums in all , how many did he solve correctly ?

- **a)** 12
- **b)** 16
- **c)** 18
- **d)** 9
- **e)** 12

**Answer: d) 9**

**Original rationale**

"explanation : suppose the boy got x sums right and 2 x sums wrong . then , x + 2 x = 27 3 x = 27 x = 9 . answer : d"

**Annotated formula**

```text
divide(27, add(const_1, const_2))
```

**Linear formula**

```text
add(const_1,const_2)|divide(n0,#0)|
```

## 93. mathqa_test_1292

Category: physics | Source: test.json, index 1292

15 beavers , working together in a constant pace , can build a dam in 4 hours . how many hours will it take 20 beavers that work at the same pace , to build the same dam ?

- **a)** 2 .
- **b)** 4 .
- **c)** 5 .
- **d)** 6
- **e)** 3 .

**Answer: e) 3 .**

**Original rationale**

"total work = 15 * 4 = 60 beaver hours 20 beaver * x = 60 beaver hours x = 60 / 20 = 3 answer : e"

**Annotated formula**

```text
divide(multiply(4, 15), 20)
```

**Linear formula**

```text
multiply(n0,n1)|divide(#0,n2)|
```

## 94. mathqa_test_1327

Category: geometry | Source: test.json, index 1327

a spirit and water solution is sold in a market . the cost per liter of the solution is directly proportional to the part ( fraction ) of spirit ( by volume ) the solution has . a solution of 1 liter of spirit and 1 liter of water costs 50 cents . how many cents does a solution of 1 liter of spirit and 3 liters of water cost ?

- **a)** 13
- **b)** 33
- **c)** 56
- **d)** 50
- **e)** 52

**Answer: d) 50**

**Original rationale**

c . 50 cents yes , ensure that you understand the relation thoroughly ! cost per liter = k * fraction of spirit 50 cents is the cost of 2 liters of solution ( 1 part water , 1 part spirit ) . so cost per liter is 25 cents . fraction of spirit is 1 / 2 . 25 = k * ( 1 / 2 ) k = 50 cost per liter = 50 * ( 1 / 4 ) ( 1 part spirit , 3 parts water ) cost for 4 liters = 50 * ( 1 / 4 ) * 4 = 50 cents d . 50 cents

**Annotated formula**

```text
multiply(multiply(50, divide(1, add(1, 3))), add(1, 3))
```

**Linear formula**

```text
add(n0,n4)|divide(n0,#0)|multiply(n2,#1)|multiply(#0,#2)
```

## 95. mathqa_test_1328

Category: physics | Source: test.json, index 1328

two trains are running in opposite directions in the same speed . the length of each train is 120 meter . if they cross each other in 12 seconds , the speed of each train ( in km / hr ) is

- **a)** 30 km / hr
- **b)** 36 km / hr
- **c)** 80 km / hr
- **d)** 90 km / hr
- **e)** none of these

**Answer: b) 36 km / hr**

**Original rationale**

"explanation : distance covered = 120 + 120 = 240 m time = 12 s let the speed of each train = x . then relative velocity = x + x = 2 x 2 x = distance / time = 240 / 12 = 20 m / s speed of each train = x = 20 / 2 = 10 m / s = 10 * 18 / 5 km / hr = 36 km / hr option b"

**Annotated formula**

```text
multiply(const_3_6, divide(divide(add(120, 120), 12), const_2))
```

**Linear formula**

```text
add(n0,n0)|divide(#0,n1)|divide(#1,const_2)|multiply(#2,const_3_6)|
```

## 96. mathqa_test_1378

Category: general | Source: test.json, index 1378

a company wants to spend equal amounts of money for the purchase of two types of computer printers costing $ 300 and $ 200 per unit , respectively . what is the fewest number of computer printers that the company can purchase ?

- **a)** 3
- **b)** 5
- **c)** 7
- **d)** 9
- **e)** 11

**Answer: b) 5**

**Original rationale**

"the smallest amount that the company can spend is the lcm of 300 and 200 , which is 600 for each , which is total 1200 . the number of 1 st type of computers which costing $ 300 = 600 / 300 = 2 . the number of 2 nd type of computers which costing $ 200 = 600 / 200 = 3 . total = 2 + 3 = 5 answer is b ."

**Annotated formula**

```text
add(divide(lcm(300, 200), 300), divide(lcm(300, 200), 200))
```

**Linear formula**

```text
lcm(n0,n1)|divide(#0,n0)|divide(#0,n1)|add(#1,#2)|
```

## 97. mathqa_test_1393

Category: general | Source: test.json, index 1393

the price of a certain product increased by the same percent from 1960 to 1970 as from 1970 to 1980 . if its price of $ 1.20 in 1970 was 150 percent of its price in 1960 , what was its price in 1980 ?

- **a)** $ 1.80
- **b)** $ 2.00
- **c)** $ 2.40
- **d)** $ 2.70
- **e)** $ 3.00

**Answer: a) $ 1.80**

**Original rationale**

the price in 1970 was 150 percent of its price in 1960 , means that the percent increase was 50 % from 1960 to 1970 ( and from 1970 to 1980 ) . therefore the price in 1980 = $ 1.2 * 1.5 = $ 1.8 . answer : a .

**Annotated formula**

```text
multiply(divide(150, const_100), 1.2)
```

**Linear formula**

```text
divide(n6,const_100)|multiply(n4,#0)
```

## 98. mathqa_test_1408

Category: general | Source: test.json, index 1408

a team of 8 persons joins in a shooting competition . the best marksman scored 85 points . if he had scored 92 points , the average score for the team would have been 84 . the number of points , the team scored was :

- **a)** 665
- **b)** 376
- **c)** 998
- **d)** 1277
- **e)** 1991

**Answer: a) 665**

**Original rationale**

explanation : let the total score be x . ( x + 92 - 85 ) / 8 = 84 . so , x + 7 = 672 = > x = 665 . answer : a ) 665

**Annotated formula**

```text
subtract(add(multiply(84, 8), 85), 92)
```

**Linear formula**

```text
multiply(n0,n3)|add(n1,#0)|subtract(#1,n2)
```

## 99. mathqa_test_1455

Category: geometry | Source: test.json, index 1455

find the volume and surface area of a cuboid 16 m long , 14 m broad and 7 m high .

- **a)** 878 cm ^ 2
- **b)** 858 cm ^ 2
- **c)** 838 cm ^ 2
- **d)** 868 cm ^ 2
- **e)** none of them

**Answer: d) 868 cm ^ 2**

**Original rationale**

volume = ( 16 x 14 x 7 ) m ^ 3 = 1568 m ^ 3 . surface area = [ 2 ( 16 x 14 + 14 x 7 + 16 x 7 ) ] cm ^ 2 = ( 2 x 434 ) cm ^ 2 = 868 cm ^ 2 . answer is d

**Annotated formula**

```text
multiply(add(multiply(16, 7), add(multiply(16, 14), multiply(14, 7))), const_2)
```

**Linear formula**

```text
multiply(n0,n1)|multiply(n1,n2)|multiply(n0,n2)|add(#0,#1)|add(#3,#2)|multiply(#4,const_2)
```

## 100. mathqa_test_1470

Category: general | Source: test.json, index 1470

village p ’ s population is 1150 greater than village q ' s population . if village q ’ s population were reduced by 200 people , then village p ’ s population would be 4 times as large as village q ' s population . what is village q ' s current population ?

- **a)** 600
- **b)** 625
- **c)** 650
- **d)** 675
- **e)** 700

**Answer: c) 650**

**Original rationale**

p = q + 1150 . p = 4 ( q - 200 ) . 4 ( q - 200 ) = q + 1150 . 3 q = 1950 . q = 650 . the answer is c .

**Annotated formula**

```text
divide(add(1150, multiply(200, 4)), const_3)
```

**Linear formula**

```text
multiply(n1,n2)|add(n0,#0)|divide(#1,const_3)
```

## 101. mathqa_test_1481

Category: physics | Source: test.json, index 1481

ajay can walk 4 km in 1 hour . in how many hours he can walk 40 km ?

- **a)** 5 hrs
- **b)** 10 hrs
- **c)** 15 hrs
- **d)** 20 hrs
- **e)** 30 hrs

**Answer: b) 10 hrs**

**Original rationale**

"1 hour he walk 4 km he walk 40 km in = 40 / 4 * 1 = 10 hours answer is b"

**Annotated formula**

```text
divide(40, 4)
```

**Linear formula**

```text
divide(n2,n0)|
```

## 102. mathqa_test_1482

Category: general | Source: test.json, index 1482

ramesh has solved 108 questions in an examination . if he got only ‘ 0 ’ marks , then how many questions were wrong when one mark is given for each one correct answer and 1 / 3 mark is subtracted on each wrong answer .

- **a)** 78
- **b)** 79
- **c)** 80
- **d)** 81
- **e)** 82

**Answer: d) 81**

**Original rationale**

if ramesh attempts ' x ' questions correct and ' y ' questions wrong , then x + y = 108 - - - ( i ) & x - ( 1 / 3 ) y = 0 - - - ( ii ) on solving x = 27 , y = 81 answer : d

**Annotated formula**

```text
subtract(108, divide(multiply(divide(1, 3), 108), add(const_1, divide(1, 3))))
```

**Linear formula**

```text
divide(n2,n3)|add(#0,const_1)|multiply(n0,#0)|divide(#2,#1)|subtract(n0,#3)
```

## 103. mathqa_test_1486

Category: gain | Source: test.json, index 1486

a circle graph shows how the megatech corporation allocates its research and development budget : 17 % microphotonics ; 24 % home electronics ; 15 % food additives ; 29 % genetically modified microorganisms ; 8 % industrial lubricants ; and the remainder for basic astrophysics . if the arc of each sector of the graph is proportional to the percentage of the budget it represents , how many degrees of the circle are used to represent basic astrophysics research ?

- **a)** 8 °
- **b)** 10 °
- **c)** 26 °
- **d)** 36 °
- **e)** 52 °

**Answer: c) 26 °**

**Original rationale**

here all percentage when summed we need to get 100 % . as per data 17 + 24 + 15 + 29 + 8 = 93 % . so remaining 7 % is the balance for the astrophysics . since this is a circle all percentage must be equal to 360 degrees . 100 % - - - - 360 degrees then 7 % will be 26 degrees . . imo option c .

**Annotated formula**

```text
divide(multiply(subtract(const_100, add(add(add(add(17, 24), 15), 29), 8)), divide(const_3600, const_10)), const_100)
```

**Linear formula**

```text
add(n0,n1)|divide(const_3600,const_10)|add(n2,#0)|add(n3,#2)|add(n4,#3)|subtract(const_100,#4)|multiply(#1,#5)|divide(#6,const_100)
```

## 104. mathqa_test_1494

Category: general | Source: test.json, index 1494

a fruit - salad mixture consists of apples , peaches , and grapes in the ratio 9 : 6 : 5 , respectively , by weight . if 40 pounds of the mixture is prepared , the mixture includes how many more pounds of apples than grapes ?

- **a)** 15
- **b)** 12
- **c)** 8
- **d)** 6
- **e)** 4

**Answer: c) 8**

**Original rationale**

we can first set up our ratio using variable multipliers . we are given that a fruit - salad mixture consists of apples , peaches , and grapes , in the ratio of 6 : 5 : 2 , respectively , by weight . thus , we can say : apples : peaches : grapes = 6 x : 5 x : 2 x we are given that 39 pounds of the mixture is prepared so we can set up the following question and determine a value for x : 9 x + 6 x + 5 x = 40 20 x = 40 x = 2 now we can determine the number of pounds of apples and of grapes . pounds of grapes = ( 5 ) ( 2 ) = 10 pounds of apples = ( 9 ) ( 2 ) = 18 thus we know that there are 18 – 10 = 8 more pounds of apples than grapes . answer is c .

**Annotated formula**

```text
subtract(multiply(9, const_2), multiply(5, const_2))
```

**Linear formula**

```text
multiply(n0,const_2)|multiply(n2,const_2)|subtract(#0,#1)
```

## 105. mathqa_test_1516

Category: general | Source: test.json, index 1516

given a + b = 1 , find the value of 2 a + 2 b . two solutions are presented below . only one is correct , even though both yield the correct answer .

- **a)** 3
- **b)** 5
- **c)** 4
- **d)** 2
- **e)** 1

**Answer: d) 2**

**Original rationale**

because a + b = 1 , 2 a + 2 b = 2 ( a + b ) = 2 × 1 = 2 . correct answer d

**Annotated formula**

```text
subtract(add(add(2, 1), 2), add(2, 1))
```

**Linear formula**

```text
add(n0,n1)|add(n1,#0)|subtract(#1,#0)
```

## 106. mathqa_test_1531

Category: general | Source: test.json, index 1531

which is the least number that must be subtracted from 1856 so that the remainder when divided by 7 , 12 , 10 is 4 ?

- **a)** 168
- **b)** 172
- **c)** 182
- **d)** 140
- **e)** 160

**Answer: b) 172**

**Original rationale**

first we need to figure out what numbers are exactly divisible by 7 , 12,10 . this will be the set { lcm , lcmx 2 , lcmx 3 , . . . } lcm ( 7 , 12,10 ) = 42 * 10 = 420 the numbers which will leave remainder 4 will be { 420 + 4 , 420 x 2 + 4 , , . . . } the largest such number less than or equal to 1856 is 420 * 4 + 4 or 1684 to obtain this you need to subtract 172 . b

**Annotated formula**

```text
subtract(1856, add(4, multiply(gcd(1856, lcm(lcm(7, 12), 10)), lcm(lcm(7, 12), 10))))
```

**Linear formula**

```text
lcm(n1,n2)|lcm(n3,#0)|gcd(n0,#1)|multiply(#2,#1)|add(n4,#3)|subtract(n0,#4)
```

## 107. mathqa_test_1550

Category: physics | Source: test.json, index 1550

the diameter of the driving wheel of a bus in 140 cm . how many revolutions per minute must the wheel make in order to keep a speed of 66 kmph ?

- **a)** 210
- **b)** 220
- **c)** 230
- **d)** 240
- **e)** 250

**Answer: e) 250**

**Original rationale**

"distance covered in 1 min = ( 66 * 1000 ) / 60 = 1100 m circumference of the wheel = ( 2 * ( 22 / 7 ) * . 70 ) = 4.4 m no of revolution per min = 1100 / 4.4 = 250 answer : e"

**Annotated formula**

```text
divide(divide(multiply(66, const_1000), const_60), multiply(multiply(divide(add(66, const_2), add(const_4, const_3)), const_2), divide(divide(140, const_100), const_2)))
```

**Linear formula**

```text
add(n1,const_2)|add(const_3,const_4)|divide(n0,const_100)|multiply(n1,const_1000)|divide(#3,const_60)|divide(#2,const_2)|divide(#0,#1)|multiply(#6,const_2)|multiply(#5,#7)|divide(#4,#8)|
```

## 108. mathqa_test_1554

Category: physics | Source: test.json, index 1554

two trains are moving in opposite directions with speed of 70 km / hr and 90 km / hr respectively . their lengths are 1.10 km and 0.9 km respectively . the slower train cross the faster train in - - - seconds

- **a)** 56
- **b)** 45
- **c)** 47
- **d)** 26
- **e)** 25

**Answer: b) 45**

**Original rationale**

"explanation : relative speed = 70 + 90 = 160 km / hr ( since both trains are moving in opposite directions ) total distance = 1.1 + . 9 = 2 km time = 2 / 160 hr = 1 / 80 hr = 3600 / 80 seconds = = 45 seconds answer : option b"

**Annotated formula**

```text
multiply(divide(add(1.10, 0.9), add(70, 90)), const_3600)
```

**Linear formula**

```text
add(n2,n3)|add(n0,n1)|divide(#0,#1)|multiply(#2,const_3600)|
```

## 109. mathqa_test_1556

Category: general | Source: test.json, index 1556

a certain experimental mathematics program was tried out in 2 classes in each of 26 elementary schools and involved 32 teachers . each of the classes had 1 teacher and each of the teachers taught at least 1 , but not more than 3 , of the classes . if the number of teachers who taught 3 classes is n , then the least and greatest possible values of n , respectively , are

- **a)** 0 and 13
- **b)** 0 and 14
- **c)** 1 and 10
- **d)** 1 and 9
- **e)** 2 and 8

**Answer: c) 1 and 10**

**Original rationale**

"one may notice that greatest possible values differ in each answer choice in contrast to the least values , which repeat . to find out the greatest value you should count the total classes ( 26 * 2 = 52 ) , then subtract the total # of teachers since we know from the question that each teacher taught at least one class ( 52 - 32 = 20 ) . thus we get a number of the available extra - classes for teachers , and all that we need is just to count how many teachers could take 2 more classes , which is 20 / 2 = 10 . so the greatest possible value of the # of teachers who had 3 classes is 10 . only answer c has this option ."

**Annotated formula**

```text
divide(subtract(multiply(26, 2), 32), 2)
```

**Linear formula**

```text
multiply(n0,n1)|subtract(#0,n2)|divide(#1,n0)|
```

## 110. mathqa_test_1563

Category: gain | Source: test.json, index 1563

a shopkeeper forced to sell at cost price , uses a 800 grams weight for a kilogram . what is his gain percent ?

- **a)** 10 %
- **b)** 25 %
- **c)** 11.11 %
- **d)** 12 %
- **e)** none of these

**Answer: b) 25 %**

**Original rationale**

"shopkeeper sells 800 g instead of 1000 g . so , his gain = 1000 - 800 = 200 g . thus , % gain = 200 * 100 ) / 800 = 25 % . answer : option b"

**Annotated formula**

```text
multiply(divide(add(multiply(const_2, const_100), divide(const_100, const_2)), 800), const_100)
```

**Linear formula**

```text
divide(const_100,const_2)|multiply(const_100,const_2)|add(#0,#1)|divide(#2,n0)|multiply(#3,const_100)|
```

## 111. mathqa_test_1576

Category: gain | Source: test.json, index 1576

a merchant gets a 5 % discount on each meter of fabric he buys after the first 2,000 meters and a 7 % discount on every meter after the next 1,500 meters . the price , before discount , of one meter of fabric is $ 2 , what is the total amount of money the merchant spends on 5,000 meters of fabric ?

- **a)** $ 8280
- **b)** $ 8520
- **c)** $ 8710
- **d)** $ 8930
- **e)** $ 9640

**Answer: e) $ 9640**

**Original rationale**

"for first 2000 meters he does not get any discount . the price is 2 * 2000 = $ 4000 for next 1500 meters , he gets a 5 % discount . the price is 1.9 * 1500 = $ 2850 for the next 1500 meters , he gets a 7 % discount . the price is 1.86 * 1500 = $ 2790 the total price is $ 4000 + $ 2850 + $ 2790 = $ 9640 the answer is e ."

**Annotated formula**

```text
multiply(multiply(2, const_3), const_100)
```

**Linear formula**

```text
multiply(n4,const_3)|multiply(#0,const_100)|
```

## 112. mathqa_test_1620

Category: physics | Source: test.json, index 1620

a train 120 m long is running with a speed of 62 kmph . in what time will it pass a man who is running at 8 kmph in the same direction in which the train is going

- **a)** 5 sec
- **b)** 6 sec
- **c)** 7 sec
- **d)** 8 sec
- **e)** 9 sec

**Answer: d) 8 sec**

**Original rationale**

"explanation : speed of the train relative to man = ( 62 - 8 ) kmph = ( 54 × 5 / 18 ) m / sec = 15 m / sec time taken by the train to cross the man = time taken by it to cover 120 m at 15 m / sec = 120 × 1 / 15 sec = 8 sec answer : option d"

**Annotated formula**

```text
divide(120, multiply(add(62, 8), const_0_2778))
```

**Linear formula**

```text
add(n1,n2)|multiply(#0,const_0_2778)|divide(n0,#1)|
```

## 113. mathqa_test_1635

Category: general | Source: test.json, index 1635

in a certain game , a large container is filled with red , yellow , green , and blue beads worth , respectively , 7 , 5 , 3 , and 2 points each . a number of beads are then removed from the container . if the product of the point values of the removed beads is 30 , 870000 , how many red beads were removed ?

- **a)** 1
- **b)** 2
- **c)** 3
- **d)** 4
- **e)** 5

**Answer: c) 3**

**Original rationale**

30 , 870,000 = 2 ^ 4 * 5 ^ 4 * 3087 = 2 ^ 4 * 3 * 5 ^ 4 * 1029 = 2 ^ 4 * 3 ^ 2 * 5 ^ 4 * 343 = 2 ^ 4 * 3 ^ 2 * 5 ^ 4 * 7 ^ 3 the answer is c .

**Annotated formula**

```text
divide(multiply(3, const_1), const_1)
```

**Linear formula**

```text
multiply(n2,const_1)|divide(#0,const_1)
```

## 114. mathqa_test_1643

Category: general | Source: test.json, index 1643

( 0.15 ) ( power 3 ) - ( 0.1 ) ( power 3 ) / ( 0.15 ) ( power 2 ) + 0.015 + ( 0.1 ) ( power 2 ) is :

- **a)** 0.68
- **b)** 0.08
- **c)** 0.05
- **d)** 0.06
- **e)** none of them

**Answer: c) 0.05**

**Original rationale**

"given expression = ( 0.15 ) ( power 3 ) - ( 0.1 ) ( power 3 ) / ( 0.15 ) ( power 2 ) + ( 0.15 x 0.1 ) + ( 0.1 ) ( power 2 ) = a ( power 3 ) - b ( power 3 ) / a ( power 2 ) + ab + b ( power 2 ) = ( a - b ) = ( 0.15 - 0.1 ) = 0.05 answer is c ."

**Annotated formula**

```text
divide(subtract(power(0.15, 3), power(0.1, 3)), add(add(power(0.15, 2), 0.015), power(0.1, 2)))
```

**Linear formula**

```text
power(n0,n1)|power(n2,n1)|power(n0,n5)|power(n2,n5)|add(n6,#2)|subtract(#0,#1)|add(#4,#3)|divide(#5,#6)|
```

## 115. mathqa_test_1718

Category: general | Source: test.json, index 1718

a group of 55 adults and 70 children go for trekking . if there is meal for either 70 adults or 90 children and if 28 adults have their meal , find the total number of children that can be catered with the remaining food .

- **a)** 33
- **b)** 54
- **c)** 18
- **d)** 17
- **e)** 01

**Answer: b) 54**

**Original rationale**

"explanation : as there is meal for 70 adults and 28 have their meal , the meal left can be catered to 42 adults . now , 70 adults = 90 children 7 adults = 9 children therefore , 42 adults = 54 children hence , the meal can be catered to 54 children . answer : b"

**Annotated formula**

```text
multiply(subtract(70, 28), divide(90, 70))
```

**Linear formula**

```text
divide(n3,n1)|subtract(n1,n4)|multiply(#0,#1)|
```

## 116. mathqa_test_1728

Category: physics | Source: test.json, index 1728

a , b , c , d and e are 5 consecutive points on a straight line . if bc = 2 cd , de = 5 , ab = 5 and ac = 11 , what is the length of ae ?

- **a)** 19
- **b)** 21
- **c)** 23
- **d)** 25
- **e)** 27

**Answer: a) 19**

**Original rationale**

"ac = 11 and ab = 5 , so bc = 6 . bc = 2 cd so cd = 3 . the length of ae is ab + bc + cd + de = 5 + 6 + 3 + 5 = 19 the answer is a ."

**Annotated formula**

```text
add(add(11, divide(subtract(11, 5), 2)), 5)
```

**Linear formula**

```text
subtract(n4,n0)|divide(#0,n1)|add(n4,#1)|add(n2,#2)|
```

## 117. mathqa_test_1729

Category: physics | Source: test.json, index 1729

a can run 288 metre in 28 seconds and b in 32 seconds . by what distance a beat b ?

- **a)** 38 metre
- **b)** 28 metre
- **c)** 23 metre
- **d)** 15 metre
- **e)** 36 metre

**Answer: e) 36 metre**

**Original rationale**

"clearly , a beats b by 4 seconds now find out how much b will run in these 4 seconds speed of b = distance / time taken by b = 288 / 32 = 9 m / s distance covered by b in 4 seconds = speed ã — time = 9 ã — 4 = 36 metre i . e . , a beat b by 36 metre answer is e"

**Annotated formula**

```text
subtract(288, multiply(divide(288, 32), 28))
```

**Linear formula**

```text
divide(n0,n2)|multiply(n1,#0)|subtract(n0,#1)|
```

## 118. mathqa_test_1731

Category: general | Source: test.json, index 1731

if x / y = 7 / 4 , then ( x + y ) / ( x - y ) = ?

- **a)** 5
- **b)** 11 / 3
- **c)** - 1 / 6
- **d)** - 1 / 5
- **e)** - 5

**Answer: b) 11 / 3**

**Original rationale**

"any x and y satisfying x / y = 7 / 4 should give the same value for ( x + y ) / ( x - y ) . say x = 7 and y = 4 , then ( x + y ) / ( x - y ) = ( 7 + 4 ) / ( 7 - 4 ) = 11 / 3 . answer : b ."

**Annotated formula**

```text
divide(add(7, 4), subtract(7, 4))
```

**Linear formula**

```text
add(n0,n1)|subtract(n0,n1)|divide(#0,#1)|
```

## 119. mathqa_test_1754

Category: gain | Source: test.json, index 1754

on a sum of money , the simple interest for 2 years is rs . 324 , while the compound interest is rs . 340 , the rate of interest being the same in both the cases . the rate of interest is

- **a)** 15 %
- **b)** 14.25 %
- **c)** 9.87 %
- **d)** 10.5 %
- **e)** 11.5 %

**Answer: c) 9.87 %**

**Original rationale**

"the difference between compound interest and simple interest on rs . p for 2 years at r % per annum = ( r ã — si ) / ( 2 ã — 100 ) difference between the compound interest and simple interest = 340 - 324 = 16 ( r ã — si ) / ( 2 ã — 100 ) = 16 ( r ã — 324 ) / ( 2 ã — 100 ) = 16 r = 9.87 % answer : option c"

**Annotated formula**

```text
divide(multiply(const_100, subtract(subtract(340, divide(324, 2)), divide(324, 2))), divide(324, 2))
```

**Linear formula**

```text
divide(n1,n0)|subtract(n2,#0)|subtract(#1,#0)|multiply(#2,const_100)|divide(#3,#0)|
```

## 120. mathqa_test_1780

Category: general | Source: test.json, index 1780

what is the largest number of 4 digits which is divisible by 15 , 25 , 40 and 75 ?

- **a)** 9600
- **b)** 5200
- **c)** 362
- **d)** 958
- **e)** 258

**Answer: a) 9600**

**Original rationale**

explanation : largest number of four digits = 9999 lcm of 15 , 25 , 40 and 75 = 600 9999 ÷ 600 = 16 , remainder = 399 hence , largest number of four digits which is divisible by 15 , 25 , 40 and 75 = 9999 - 399 = 9600 answer : a

**Annotated formula**

```text
subtract(subtract(multiply(const_100, const_100), const_1), reminder(subtract(multiply(const_100, const_100), const_1), lcm(lcm(lcm(15, 25), 40), 75)))
```

**Linear formula**

```text
lcm(n1,n2)|multiply(const_100,const_100)|lcm(n3,#0)|subtract(#1,const_1)|lcm(n4,#2)|reminder(#3,#4)|subtract(#3,#5)
```

## 121. mathqa_test_1839

Category: other | Source: test.json, index 1839

the l . c . m of two numbers is 48 . the numbers are in the ratio 2 : 3 . the sum of numbers is :

- **a)** 28
- **b)** 30
- **c)** 40
- **d)** 50
- **e)** 60

**Answer: c) 40**

**Original rationale**

"let the numbers be 2 x and 3 x . then , their l . c . m = 6 x . so , 6 x = 48 or x = 8 . the numbers are 16 and 24 . hence , required sum = ( 16 + 24 ) = 40 . answer : c"

**Annotated formula**

```text
divide(multiply(2, 48), 3)
```

**Linear formula**

```text
multiply(n0,n1)|divide(#0,n2)|
```

## 122. mathqa_test_1857

Category: general | Source: test.json, index 1857

what is the median of a set of consecutive integers if the sum of nth number from the beginning and nth number from the end is 150 ?

- **a)** 10
- **b)** 25
- **c)** 50
- **d)** 75
- **e)** 100

**Answer: d) 75**

**Original rationale**

"surprisingly no one answered this easy one . property of a set of consecutive integerz . mean = median = ( first element + last element ) / 2 = ( second element + last but one element ) / 2 = ( third element + third last element ) / 2 etc . etc . so mean = median = 150 / 2 = 75 answer is d"

**Annotated formula**

```text
divide(150, const_2)
```

**Linear formula**

```text
divide(n0,const_2)|
```

## 123. mathqa_test_1858

Category: physics | Source: test.json, index 1858

two trains running in opposite directions cross a man standing on the platform in 27 seconds and 17 seconds respectively and they cross each other in 25 seconds . the ratio of their speeds is ?

- **a)** 3 / 1
- **b)** 4 / 1
- **c)** 3 / 3
- **d)** 3 / 5
- **e)** 5 / 2

**Answer: b) 4 / 1**

**Original rationale**

"let the speeds of the two trains be x m / sec and y m / sec respectively . then , length of the first train = 27 x meters , and length of the second train = 17 y meters . ( 27 x + 17 y ) / ( x + y ) = 25 = = > 27 x + 17 y = 25 x + 25 y = = > 2 x = 8 y = = > x / y = 4 / 1 . answer : b"

**Annotated formula**

```text
divide(subtract(27, 25), subtract(25, 17))
```

**Linear formula**

```text
subtract(n0,n2)|subtract(n2,n1)|divide(#0,#1)|
```

## 124. mathqa_test_1879

Category: physics | Source: test.json, index 1879

a train which has 420 m long , is running 45 kmph . in what time will it cross a person moving at 9 kmph in same direction ?

- **a)** 56 sec
- **b)** 42 sec
- **c)** 36 sec
- **d)** 29 sec .
- **e)** 19 sec .

**Answer: b) 42 sec**

**Original rationale**

"time taken to cross a moving person = length of train / relative speed time taken = 420 / ( ( 45 - 9 ) ( 5 / 18 ) = 420 / 36 * ( 5 / 18 ) = 420 / 10 = 42 sec answer : b"

**Annotated formula**

```text
divide(420, subtract(divide(45, const_3_6), divide(divide(9, const_2), const_3_6)))
```

**Linear formula**

```text
divide(n1,const_3_6)|divide(n2,const_2)|divide(#1,const_3_6)|subtract(#0,#2)|divide(n0,#3)|
```

## 125. mathqa_test_1881

Category: general | Source: test.json, index 1881

sum of the squares of 3 no . is 276 and the sum of their products taken two at a time is 150 . find the sum ?

- **a)** 22
- **b)** 18
- **c)** 26
- **d)** 24
- **e)** 32

**Answer: d) 24**

**Original rationale**

"( a + b + c ) 2 = a 2 + b 2 + c 2 + 2 ( ab + bc + ca ) = 276 + 2 * 150 a + b + c = â ˆ š 576 = 24 answer d"

**Annotated formula**

```text
sqrt(add(276, multiply(150, const_2)))
```

**Linear formula**

```text
multiply(n2,const_2)|add(n1,#0)|sqrt(#1)|
```

## 126. mathqa_test_1893

Category: physics | Source: test.json, index 1893

the lcm and hcf of two numbers are 8 and 48 respectively . if one of them is 24 , find the other ?

- **a)** 12
- **b)** 14
- **c)** 15
- **d)** 16
- **e)** 20

**Answer: d) 16**

**Original rationale**

hcf x lcm = product of numbers 8 x 48 = 24 x the other number other number = ( 8 x 48 ) / 24 other number = 16 answer : d

**Annotated formula**

```text
divide(multiply(8, 48), 24)
```

**Linear formula**

```text
multiply(n0,n1)|divide(#0,n2)
```

## 127. mathqa_test_1917

Category: physics | Source: test.json, index 1917

the time taken by a man to row his boat upstream is twice the time taken by him to row the same distance downstream . if the speed of the boat in still water is 45 kmph , find the speed of the stream ?

- **a)** 12 kmph
- **b)** 13 kmph
- **c)** 14 kmph
- **d)** 15 kmph
- **e)** 16 kmph

**Answer: d) 15 kmph**

**Original rationale**

"the ratio of the times taken is 2 : 1 . the ratio of the speed of the boat in still water to the speed of the stream = ( 2 + 1 ) / ( 2 - 1 ) = 3 / 1 = 3 : 1 speed of the stream = 45 / 3 = 15 kmph answer : d"

**Annotated formula**

```text
subtract(45, divide(multiply(45, const_2), const_3))
```

**Linear formula**

```text
multiply(n0,const_2)|divide(#0,const_3)|subtract(n0,#1)|
```

## 128. mathqa_test_1946

Category: general | Source: test.json, index 1946

in the seaside summer camp there are 50 children . 90 % of the children are boys and the rest are girls . the camp administrator decided to make the number of girls only 5 % of the total number of children in the camp . how many more boys must she bring to make that happen ?

- **a)** 50 .
- **b)** 45 .
- **c)** 40 .
- **d)** 30 .
- **e)** 25 .

**Answer: a) 50 .**

**Original rationale**

given there are 50 students in the seaside summer camp , 90 % of 50 = 45 boys and remaining 5 girls . now here 90 % are boys and 10 % are girls . now question is asking about how many boys do we need to add , to make the girls percentage to 5 or 5 % . . if we add 50 to existing 45 then the count will be 95 and the girls number will be 5 as it . now boys are 95 % and girls are 5 % . ( out of 100 students = 95 boys + 5 girls ) . imo option a is correct .

**Annotated formula**

```text
subtract(divide(multiply(subtract(50, divide(multiply(90, 50), const_100)), const_100), 5), 50)
```

**Linear formula**

```text
multiply(n0,n1)|divide(#0,const_100)|subtract(n0,#1)|multiply(#2,const_100)|divide(#3,n2)|subtract(#4,n0)
```

## 129. mathqa_test_1990

Category: general | Source: test.json, index 1990

the difference between two numbers is 1365 . when the larger number is divided by the smaller one , the quotient is 6 and the remainder is 15 . the smaller number is

- **a)** 240
- **b)** 250
- **c)** 260
- **d)** 270
- **e)** none

**Answer: d) 270**

**Original rationale**

"solution let the numbers be x and x ( x + 1365 ) . then , x + 1365 = 6 x + 15 ‹ = › 5 x = 1350 . ‹ = › x = 270 . answer d"

**Annotated formula**

```text
divide(subtract(1365, 15), subtract(6, const_1))
```

**Linear formula**

```text
subtract(n0,n2)|subtract(n1,const_1)|divide(#0,#1)|
```

## 130. mathqa_test_2001

Category: physics | Source: test.json, index 2001

a man ' s regular pay is $ 3 per hour up to 40 hours . overtime is twice the payment for regular time . if he was paid $ 174 , how many hours overtime did he work ?

- **a)** 8
- **b)** 5
- **c)** 9
- **d)** 6
- **e)** 10

**Answer: c) 9**

**Original rationale**

"at $ 3 per hour up to 40 hours , regular pay = $ 3 x 40 = $ 120 if total pay = $ 168 , overtime pay = $ 174 - $ 120 = $ 54 overtime rate ( twice regular ) = 2 x $ 3 = $ 6 per hour = > number of overtime hours = $ 54 / $ 6 = 9 ans is c"

**Annotated formula**

```text
divide(subtract(174, multiply(3, 40)), multiply(3, const_2))
```

**Linear formula**

```text
multiply(n0,n1)|multiply(n0,const_2)|subtract(n2,#0)|divide(#2,#1)|
```

## 131. mathqa_test_2021

Category: general | Source: test.json, index 2021

an angry arjun carried some arrows for fighting with bheeshm . with half the arrows , he cut down the arrows thrown by bheeshm on him and with 6 other arrows he killed the chariot driver of bheeshm . with one arrow each he knocked down respectively the chariot , the flag and the bow of bheeshm . finally , with one more than 4 times the square root of arrows he laid bheeshm unconscious on an arrow bed . find the total number of arrows arjun had .

- **a)** 90
- **b)** 100
- **c)** 110
- **d)** 120
- **e)** 130

**Answer: b) 100**

**Original rationale**

x / 2 + 6 + 3 + 1 + 4 sqrt ( x ) = x x / 2 + 10 + 4 sqrt ( x ) = x 4 sqrt ( x ) = x / 2 - 10 squaring on both sides 16 x = x ² / 4 + 100 - 10 x simplifying x ² - 104 x + 400 = 0 x = 100 , 4 x = 4 is not possible therefore x = 100 answer : b

**Annotated formula**

```text
power(add(6, 4), const_2)
```

**Linear formula**

```text
add(n0,n1)|power(#0,const_2)
```

## 132. mathqa_test_2044

Category: general | Source: test.json, index 2044

an investor can sell her microtron stock for 36 $ per share and her dynaco stock for 68 $ per share , if she sells 300 shares altogether , some of each stock , at an average price per share of 40 $ , how many shares of dynaco stock has she sold ?

- **a)** 52
- **b)** 37.5
- **c)** 92
- **d)** 136
- **e)** 184

**Answer: b) 37.5**

**Original rationale**

"w 1 / w 2 = ( a 2 - aavg ) / ( aavg - a 1 ) = ( 68 - 40 ) / ( 40 - 36 ) = 28 / 4 = 7 / 1 = number of microtron stocks / number of dynaco stocks so for every 7 microtron stock , she sold 1 dynaco stock . so out of 300 total stocks , ( 1 / 7 ) th i . e . 300 / 8 = 37.5 must be dynaco stock . answer ( b )"

**Annotated formula**

```text
divide(multiply(300, divide(40, subtract(68, 36))), divide(add(36, 68), subtract(68, 36)))
```

**Linear formula**

```text
add(n0,n1)|subtract(n1,n0)|divide(n3,#1)|divide(#0,#1)|multiply(n2,#2)|divide(#4,#3)|
```

## 133. mathqa_test_2050

Category: general | Source: test.json, index 2050

find the number which is nearest to 3105 and is exactly divisible by 21 ?

- **a)** 3100
- **b)** 2500
- **c)** 2545
- **d)** 5800
- **e)** 3108

**Answer: e) 3108**

**Original rationale**

on dividing 3105 by 21 , we get 18 as remainder . number to be added to 3105 = ( 21 - 18 ) - 3 . hence , required number = 3105 + 3 = 3108 . answer e

**Annotated formula**

```text
add(3105, subtract(21, reminder(3105, 21)))
```

**Linear formula**

```text
reminder(n0,n1)|subtract(n1,#0)|add(n0,#1)
```

## 134. mathqa_test_2069

Category: general | Source: test.json, index 2069

15 lts are taken of from a container full of liquid a and replaced with liquid b . again 15 more lts of the mixture is taken and replaced with liquid b . after this process , if the container contains liquid a and b in the ratio 9 : 16 , what is the capacity of the container h ?

- **a)** a : 45
- **b)** b : 25
- **c)** c : 37.5
- **d)** d : 36
- **e)** e : 42

**Answer: c) c : 37.5**

**Original rationale**

if you have a 37.5 liter capacity , you start with 37.5 l of a and 0 l of b . 1 st replacement after the first replacement you have 37.5 - 15 = 22.5 l of a and 15 l of b . the key is figuring out how many liters of a and b , respectively , are contained in the next 15 liters of mixture to be removed . the current ratio of a to total mixture is 22.5 / 37.5 ; expressed as a fraction this becomes ( 45 / 2 ) / ( 75 / 2 ) , or 45 / 2 * 2 / 75 . canceling the 2 s and factoring out a 5 leaves the ratio as 9 / 15 . note , no need to reduce further as we ' re trying to figure out the amount of a and b in 15 l of solution . 9 / 15 of a means there must be 6 / 15 of b . multiply each respective ratio by 15 to get 9 l of a and 6 l of b in the next 15 l removal . final replacement the next 15 l removal means 9 liters of a and 6 liters of b are removed and replaced with 15 liters of b . 22.5 - 9 = 13.5 liters of a . 15 liters of b - 6 liters + 15 more liters = 24 liters of b . test to the see if the final ratio = 9 / 16 ; 13.5 / 24 = ( 27 / 2 ) * ( 1 / 24 ) = 9 / 16 . choice c is correct .

**Annotated formula**

```text
divide(15, subtract(const_1, sqrt(divide(9, add(9, 16)))))
```

**Linear formula**

```text
add(n2,n3)|divide(n2,#0)|sqrt(#1)|subtract(const_1,#2)|divide(n0,#3)
```

## 135. mathqa_test_2079

Category: other | Source: test.json, index 2079

a certain university will select 1 of 8 candidates eligible to fill a position in the mathematics department and 2 of 12 candidates eligible to fill 2 identical positions in the computer science department . if none of the candidates is eligible for a position in both departments , how many different sets of 3 candidates are there to fill the 3 positions ?

- **a)** 340
- **b)** 380
- **c)** 472
- **d)** 528
- **e)** 630

**Answer: d) 528**

**Original rationale**

"1 c 8 * 2 c 12 = 8 * 66 = 528 the answer is ( d )"

**Annotated formula**

```text
multiply(multiply(12, 3), 8)
```

**Linear formula**

```text
multiply(n3,n5)|multiply(n1,#0)|
```

## 136. mathqa_test_2087

Category: gain | Source: test.json, index 2087

last month , john rejected 0.5 % of the products that he inspected and jane rejected 1.00 percent of the products that she inspected . if total of 0.75 percent of the products produced last month were rejected , what fraction of the products did jane inspect ?

- **a)** 1 / 6
- **b)** 1 / 2
- **c)** 5 / 8
- **d)** 5 / 4
- **e)** 15 / 16

**Answer: d) 5 / 4**

**Original rationale**

"x - fraction of products jane inspected ( 1 - x ) - fraction of products john inspected 0.8 ( x ) + 1.00 ( 1 - x ) = 0.75 0.2 x = 1.00 - 0.75 x = 0.25 / 0.2 x = 5 / 4 therefore the answer is d : 5 / 6 ."

**Annotated formula**

```text
divide(subtract(0.75, 0.5), subtract(1.00, 0.5))
```

**Linear formula**

```text
subtract(n2,n0)|subtract(n1,n0)|divide(#0,#1)|
```

## 137. mathqa_test_2161

Category: general | Source: test.json, index 2161

how many positive integers less than 50 have a reminder 5 when divided by 7 ?

- **a)** 3
- **b)** 7
- **c)** 4
- **d)** 5
- **e)** 6

**Answer: b) 7**

**Original rationale**

"take the multiples of 7 and add 5 0 x 7 + 5 = 5 . . . . 6 x 7 + 5 = 47 there are 7 numbers answer b"

**Annotated formula**

```text
divide(factorial(subtract(add(const_4, 5), const_1)), multiply(factorial(5), factorial(subtract(const_4, const_1))))
```

**Linear formula**

```text
add(n1,const_4)|factorial(n1)|subtract(const_4,const_1)|factorial(#2)|subtract(#0,const_1)|factorial(#4)|multiply(#1,#3)|divide(#5,#6)|
```

## 138. mathqa_test_2167

Category: physics | Source: test.json, index 2167

at 15 : 00 there were 20 students in the computer lab . at 15 : 03 and every three minutes after that , 3 students entered the lab . if at 15 : 10 and every ten minutes after that 9 students left the lab , how many students were in the computer lab at 15 : 44 ?

- **a)** 7
- **b)** 14
- **c)** 25
- **d)** 27
- **e)** 30

**Answer: c) 25**

**Original rationale**

"initial no of students + 3 * ( 1 + no of possible 3 minute intervals between 15 : 03 and 15 : 44 ) - 8 * ( 1 + no of possible 10 minute intervals between 15 : 10 and 15 : 44 ) 20 + 3 * 14 - 8 * 4 = 25 c"

**Annotated formula**

```text
add(subtract(add(multiply(floor(divide(44, 03)), 03), 20), multiply(floor(divide(44, 9)), 9)), 03)
```

**Linear formula**

```text
divide(n10,n4)|divide(n10,n8)|floor(#0)|floor(#1)|multiply(n4,#2)|multiply(n8,#3)|add(n2,#4)|subtract(#6,#5)|add(n4,#7)|
```

## 139. mathqa_test_2172

Category: gain | Source: test.json, index 2172

a number increased by 25 % gives 520 . the number is ?

- **a)** 216
- **b)** 316
- **c)** 616
- **d)** 516
- **e)** 416

**Answer: e) 416**

**Original rationale**

"formula = total = 100 % , increase = ` ` + ' ' decrease = ` ` - ' ' a number means = 100 % that same number increased by 25 % = 125 % 125 % - - - - - - - > 520 ( 120 ã — 4.16 = 520 ) 100 % - - - - - - - > 416 ( 100 ã — 4.16 = 416 ) option ' e '"

**Annotated formula**

```text
divide(520, add(const_1, divide(25, const_100)))
```

**Linear formula**

```text
divide(n0,const_100)|add(#0,const_1)|divide(n1,#1)|
```

## 140. mathqa_test_2181

Category: general | Source: test.json, index 2181

if w / x = 1 / 3 and w / y = 4 / 15 , then ( x + y ) / y =

- **a)** 4 / 5
- **b)** 6 / 5
- **c)** 7 / 5
- **d)** 8 / 5
- **e)** 9 / 5

**Answer: e) 9 / 5**

**Original rationale**

"w / x = 1 / 3 = > x = 3 w and w / y = 4 / 15 = > y = 15 / 4 w ( x + y ) / y = ( 3 w + 15 / 4 w ) / ( 15 / 4 w ) = ( 27 / 4 w ) / ( 15 / 4 w ) = 9 / 5 correct option : e"

**Annotated formula**

```text
add(divide(divide(4, 1), divide(15, 3)), const_1)
```

**Linear formula**

```text
divide(n2,n0)|divide(n3,n1)|divide(#0,#1)|add(#2,const_1)|
```

## 141. mathqa_test_2187

Category: other | Source: test.json, index 2187

in a zoo , the ratio of the number of cheetahs to the number 4 then what is the increase in the number of pandas ?

- **a)** 2
- **b)** 12
- **c)** 5
- **d)** 10
- **e)** 15

**Answer: b) 12**

**Original rationale**

one short cut to solve the problem is c : p = 1 : 3 c increased to 5 = > 1 : 3 = 5 : x = > x = 15 = > p increased by 12 b is the answer

**Annotated formula**

```text
subtract(multiply(4, 4), const_4)
```

**Linear formula**

```text
multiply(n0,n0)|subtract(#0,const_4)
```

## 142. mathqa_test_2196

Category: physics | Source: test.json, index 2196

there are 24 students in a seventh grade class . they decided to plant birches and roses at the school ' s backyard . while each girl planted 3 roses , every three boys planted 1 birch . by the end of the day they planted 2424 plants . how many birches were planted ?

- **a)** 2
- **b)** 5
- **c)** 8
- **d)** 6
- **e)** 4

**Answer: d) 6**

**Original rationale**

"let x be the number of roses . then the number of birches is 24 − x , and the number of boys is 3 × ( 24 − x ) . if each girl planted 3 roses , there are x 3 girls in the class . we know that there are 24 students in the class . therefore x 3 + 3 ( 24 − x ) = 24 x + 9 ( 24 − x ) = 3 ⋅ 24 x + 216 − 9 x = 72 216 − 72 = 8 x 1448 = x 1 x = 18 so , students planted 18 roses and 24 - x = 24 - 18 = 6 birches . correct answer is d ) 6"

**Annotated formula**

```text
divide(subtract(multiply(3, 24), 24), subtract(multiply(3, 3), 1))
```

**Linear formula**

```text
multiply(n0,n1)|multiply(n1,n1)|subtract(#0,n0)|subtract(#1,n2)|divide(#2,#3)|
```

## 143. mathqa_test_2199

Category: general | Source: test.json, index 2199

calculate the largest 6 digit number which is exactly divisible by 99 ?

- **a)** 999991
- **b)** 999965
- **c)** 999912
- **d)** 999936
- **e)** 999930

**Answer: d) 999936**

**Original rationale**

"largest 4 digit number is 999999 after doing 999999 ÷ 96 we get remainder 55 hence largest 4 digit number exactly divisible by 88 = 9999 - 55 = 9944 answer : d"

**Annotated formula**

```text
multiply(add(const_100, const_2), 99)
```

**Linear formula**

```text
add(const_100,const_2)|multiply(n1,#0)|
```

## 144. mathqa_test_2207

Category: physics | Source: test.json, index 2207

a certain bacteria colony doubles in size every day for 19 days , at which point it reaches the limit of its habitat and can no longer grow . if two bacteria colonies start growing simultaneously , how many days will it take them to reach the habitat ’ s limit ?

- **a)** 6.33
- **b)** 7.5
- **c)** 10
- **d)** 18
- **e)** 19

**Answer: d) 18**

**Original rationale**

"if there is one bacteria colony , then it will reach the limit of its habitat in 20 days . if there are two bacteria colonies , then in order to reach the limit of habitat they would need to double one time less than in case with one colony . thus colonies need to double 18 times . answer : d . similar questions to practice : hope it helps ."

**Annotated formula**

```text
subtract(19, divide(19, 19))
```

**Linear formula**

```text
divide(n0,n0)|subtract(n0,#0)|
```

## 145. mathqa_test_2209

Category: general | Source: test.json, index 2209

simplify : 0.3 * 0.3 + 0.3 * 0.3

- **a)** 0.52
- **b)** 0.42
- **c)** 0.18
- **d)** 0.64
- **e)** 0.46

**Answer: c) 0.18**

**Original rationale**

"given exp . = 0.3 * 0.3 + ( 0.3 * 0.3 ) = 0.09 + 0.09 = 0.18 answer is c ."

**Annotated formula**

```text
add(multiply(0.3, 0.3), multiply(0.3, 0.3))
```

**Linear formula**

```text
multiply(n0,n1)|multiply(n2,n3)|add(#0,#1)|
```

## 146. mathqa_test_2232

Category: other | Source: test.json, index 2232

what is the characteristic of the logarithm of 0.0000134 ?

- **a)** 5
- **b)** - 5
- **c)** 6
- **d)** - 6
- **e)** 7

**Answer: b) - 5**

**Original rationale**

log ( 0.0000134 ) . since there are four zeros between the decimal point and the first significant digit , the characteristic is – 5 . answer : b

**Annotated formula**

```text
floor(divide(log(0.0000134), log(const_10)))
```

**Linear formula**

```text
log(n0)|log(const_10)|divide(#0,#1)|floor(#2)
```

## 147. mathqa_test_2233

Category: general | Source: test.json, index 2233

in the game of dubblefud , red chips , blue chips and green chips are each worth 2 , 4 and 5 points respectively . in a certain selection of chips , the product of the point values of the chips is 16000 . if the number of blue chips in this selection doubles the number of green chips , how many red chips are in the selection ?

- **a)** 1
- **b)** 2
- **c)** 3
- **d)** 4
- **e)** 5

**Answer: b) 2**

**Original rationale**

this is equivalent to : - 2 x * 4 y * 5 z = 16000 y / 2 = z ( given ) 2 x * 4 y * 5 y / 2 = 16000 2 x * y ^ 2 = 16000 / 10 2 x * y ^ 2 = 1600 now from options given we will figure out which number will divide 800 and gives us a perfect square : - which gives us x = 2 as 2 * 2 * y ^ 2 = 1600 y ^ 2 = 400 y = 20 number of red chips = 2 hence b

**Annotated formula**

```text
divide(multiply(multiply(power(2, 4), power(2, const_3)), power(5, const_3)), multiply(power(const_2, multiply(2, const_3)), power(5, const_3)))
```

**Linear formula**

```text
multiply(n0,const_3)|power(n0,n1)|power(n0,const_3)|power(n2,const_3)|multiply(#1,#2)|power(const_2,#0)|multiply(#4,#3)|multiply(#5,#3)|divide(#6,#7)
```

## 148. mathqa_test_2251

Category: gain | Source: test.json, index 2251

a sells a cricket bat to b at a profit of 20 % . b sells it to c at a profit of 25 % . if c pays $ 225 for it , the cost price of the cricket bat for a is :

- **a)** 150
- **b)** 120
- **c)** 130
- **d)** 160
- **e)** 210

**Answer: a) 150**

**Original rationale**

"a 150 125 % of 120 % of a = 225 125 / 100 * 120 / 100 * a = 225 a = 225 * 2 / 3 = 150 ."

**Annotated formula**

```text
divide(225, multiply(add(const_1, divide(20, const_100)), add(const_1, divide(25, const_100))))
```

**Linear formula**

```text
divide(n0,const_100)|divide(n1,const_100)|add(#0,const_1)|add(#1,const_1)|multiply(#2,#3)|divide(n2,#4)|
```

## 149. mathqa_test_2261

Category: general | Source: test.json, index 2261

the product of two numbers is 468 and the sum of their squares is 289 . the sum of the number is ?

- **a)** a ) 23
- **b)** b ) 25
- **c)** c ) 27
- **d)** d ) 31
- **e)** e ) 35

**Answer: e) e ) 35**

**Original rationale**

"let the numbers be x and y . then , xy = 468 and x 2 + y 2 = 289 . ( x + y ) 2 = x 2 + y 2 + 2 xy = 289 + ( 2 x 468 ) = 1225 x + y = 35 . option e"

**Annotated formula**

```text
sqrt(add(power(sqrt(subtract(289, multiply(const_2, 468))), const_2), multiply(const_4, 468)))
```

**Linear formula**

```text
multiply(n0,const_4)|multiply(n0,const_2)|subtract(n1,#1)|sqrt(#2)|power(#3,const_2)|add(#0,#4)|sqrt(#5)|
```

## 150. mathqa_test_2266

Category: gain | Source: test.json, index 2266

one fourth of a solution that was 10 % salt by weight was replaced by a second solution resulting in a solution that was 16 percent sugar by weight . the second solution was what percent salt by weight ?

- **a)** 24 %
- **b)** 34 %
- **c)** 22 %
- **d)** 18 %
- **e)** 8.5 %

**Answer: b) 34 %**

**Original rationale**

"say the second solution ( which was 1 / 4 th of total ) was x % salt , then 3 / 4 * 0.1 + 1 / 4 * x = 1 * 0.16 - - > x = 0.34 . alternately you can consider total solution to be 100 liters and in this case you ' ll have : 75 * 0.1 + 25 * x = 100 * 0.16 - - > x = 0.34 . answer : b ."

**Annotated formula**

```text
multiply(subtract(multiply(divide(16, const_100), const_4), subtract(multiply(divide(10, const_100), const_4), divide(10, const_100))), const_100)
```

**Linear formula**

```text
divide(n1,const_100)|divide(n0,const_100)|multiply(#0,const_4)|multiply(#1,const_4)|subtract(#3,#1)|subtract(#2,#4)|multiply(#5,const_100)|
```

## 151. mathqa_test_2281

Category: gain | Source: test.json, index 2281

rs . 850 becomes rs . 956 in 3 years at a certain rate of simple interest . if the rate of interest is increased by 4 % , what amount will rs . 850 become in 3 years ?

- **a)** rs . 1020.80
- **b)** rs . 1025
- **c)** rs . 1058
- **d)** data inadequate
- **e)** none of these

**Answer: c) rs . 1058**

**Original rationale**

"solution s . i . = rs . ( 956 - 850 ) = rs . 106 rate = ( 100 x 106 / 850 x 3 ) = 212 / 51 % new rate = ( 212 / 51 + 4 ) % = 416 / 51 % new s . i . = rs . ( 850 x 416 / 51 x 3 / 100 ) rs . 208 . ∴ new amount = rs . ( 850 + 208 ) = rs . 1058 . answer c"

**Annotated formula**

```text
add(850, divide(multiply(multiply(850, add(divide(multiply(subtract(956, 850), const_100), multiply(850, 3)), 4)), 3), const_100))
```

**Linear formula**

```text
multiply(n0,n2)|subtract(n1,n0)|multiply(#1,const_100)|divide(#2,#0)|add(n3,#3)|multiply(n0,#4)|multiply(n2,#5)|divide(#6,const_100)|add(n0,#7)|
```

## 152. mathqa_test_2298

Category: physics | Source: test.json, index 2298

working together , printer a and printer b would finish the task in 15 minutes . printer a alone would finish the task in 45 minutes . how many pages does the task contain if printer b prints 3 pages a minute more than printer a ?

- **a)** 125
- **b)** 135
- **c)** 145
- **d)** 155
- **e)** 165

**Answer: b) 135**

**Original rationale**

"15 * a + 15 * b = x pages in 15 mins printer a will print = 15 / 45 * x pages = 1 / 3 * x pages thus in 15 mins printer printer b will print x - 1 / 3 * x = 2 / 3 * x pages also it is given that printer b prints 3 more pages per min that printer a . in 15 mins printer b will print 45 more pages than printer a thus 2 / 3 * x - 1 / 3 * x = 45 = > x = 135 pages answer : b"

**Annotated formula**

```text
multiply(divide(3, subtract(divide(45, 15), const_1)), 45)
```

**Linear formula**

```text
divide(n1,n0)|subtract(#0,const_1)|divide(n2,#1)|multiply(#2,n1)|
```

## 153. mathqa_test_2299

Category: gain | Source: test.json, index 2299

the owner of a furniture shop charges his customer 25 % more than the cost price . if a customer paid rs . 8400 for a computer table , then what was the cost price of the computer table ?

- **a)** rs . 5725
- **b)** rs . 5275
- **c)** rs . 6275
- **d)** rs . 6720
- **e)** none of these

**Answer: d) rs . 6720**

**Original rationale**

"cp = sp * ( 100 / ( 100 + profit % ) ) = 8400 ( 100 / 125 ) = rs . 6720 . answer : d"

**Annotated formula**

```text
divide(8400, add(const_1, divide(25, const_100)))
```

**Linear formula**

```text
divide(n0,const_100)|add(#0,const_1)|divide(n1,#1)|
```

## 154. mathqa_test_2323

Category: general | Source: test.json, index 2323

49 ã — 49 ã — 49 = 7 ^ ?

- **a)** 4
- **b)** 7
- **c)** 8
- **d)** 6
- **e)** none of these

**Answer: d) 6**

**Original rationale**

"49 ã — 49 ã — 49 = 7 ? or , 7 ( 2 ) ã — 7 ( 2 ) ã — 7 ( 2 ) = 7 ? or 7 ( 6 ) = 7 ? or , ? = 6 answer d"

**Annotated formula**

```text
add(subtract(power(49, const_2), 49), subtract(power(49, const_2), 49))
```

**Linear formula**

```text
power(n0,const_2)|power(n2,const_2)|subtract(#0,n0)|subtract(#1,n2)|add(#2,#3)|
```

## 155. mathqa_test_2364

Category: general | Source: test.json, index 2364

a pupil ' s marks were wrongly entered as 35 instead of 23 . due to that the average marks for the class got increased by half . the number of pupils in the class is :

- **a)** 30
- **b)** 80
- **c)** 20
- **d)** 25
- **e)** 24

**Answer: e) 24**

**Original rationale**

let there be x pupils in the class . total increase in marks = ( x * 1 / 2 ) = x / 2 . x / 2 = ( 35 - 23 ) = > x / 2 = 12 = > x = 24 . answer : e

**Annotated formula**

```text
multiply(subtract(35, 23), const_2)
```

**Linear formula**

```text
subtract(n0,n1)|multiply(#0,const_2)
```

## 156. mathqa_test_2390

Category: probability | Source: test.json, index 2390

in a single throw of a die , what is the probability of getting a number greater than 2 ?

- **a)** 1 / 2
- **b)** 2 / 5
- **c)** 1 / 3
- **d)** 2 / 7
- **e)** 2 / 3

**Answer: e) 2 / 3**

**Original rationale**

"s = { 1,2 , 3,4 , 5,6 } e = { 3,4 , 5,6 } probability = 4 / 6 = 2 / 3 answer is e"

**Annotated formula**

```text
divide(const_2, add(2, const_2))
```

**Linear formula**

```text
add(n0,const_2)|divide(const_2,#0)|
```

## 157. mathqa_test_2394

Category: gain | Source: test.json, index 2394

a watch was sold at a loss of 10 % . if it was sold for rs . 140 more , there would have been a gain of 4 % . what is the cost price ?

- **a)** rs . 1000
- **b)** rs . 1100
- **c)** rs . 1200
- **d)** rs . 1250
- **e)** rs . 1500

**Answer: a) rs . 1000**

**Original rationale**

"explanation : 90 % 104 % - - - - - - - - 14 % - - - - 140 100 % - - - - ? = > rs . 1000 a )"

**Annotated formula**

```text
divide(multiply(140, const_100), subtract(add(const_100, 4), subtract(const_100, 10)))
```

**Linear formula**

```text
add(const_100,n2)|multiply(n1,const_100)|subtract(const_100,n0)|subtract(#0,#2)|divide(#1,#3)|
```

## 158. mathqa_test_2413

Category: general | Source: test.json, index 2413

find the number which is nearest to 3105 and is exactly divisible by 21 .

- **a)** 1208
- **b)** 3108
- **c)** 241
- **d)** 217
- **e)** 3147

**Answer: b) 3108**

**Original rationale**

"sol . on dividing 3105 by 21 , we get 18 as remainder . number to be added to 3105 = ( 21 - 18 ) - 3 . hence , required number = 3105 + 3 = 3108 . option b"

**Annotated formula**

```text
add(3105, subtract(21, reminder(3105, 21)))
```

**Linear formula**

```text
reminder(n0,n1)|subtract(n1,#0)|add(n0,#1)|
```

## 159. mathqa_test_2418

Category: general | Source: test.json, index 2418

what is the total number of integers between 20 and 100 that are divisible by 9 ?

- **a)** 5
- **b)** 15
- **c)** 12
- **d)** 7
- **e)** 9

**Answer: e) 9**

**Original rationale**

"27 , 36 , 45 , . . . , 90,99 this is an equally spaced list ; you can use the formula : n = ( largest - smallest ) / ( ' space ' ) + 1 = ( 99 - 27 ) / ( 9 ) + 1 = 8 + 1 = 9 answer is e"

**Annotated formula**

```text
add(divide(subtract(100, 20), 9), const_1)
```

**Linear formula**

```text
subtract(n1,n0)|divide(#0,n2)|add(#1,const_1)|
```

## 160. mathqa_test_2440

Category: gain | Source: test.json, index 2440

in a certain pond , 80 fish were caught , tagged , and returned to the pond . a few days later , 50 fish were caught again , of which 2 were found to have been tagged . if the percent of tagged fish in the second catch approximates the percent of tagged fish in the pond , what is the approximate number of fish in the pond ?

- **a)** 400
- **b)** 625
- **c)** 1,250
- **d)** 2,000
- **e)** 10,000

**Answer: d) 2,000**

**Original rationale**

this is a rather straight forward ratio problem . 1 . 80 fish tagged 2 . 2 out of the 50 fish caught were tagged thus 2 / 50 2 / 50 = 80 / x thus , x = 2000 think of the analogy : 2 fish is to 50 fish as 50 fish is to . . . ? you ' ve tagged 50 fish and you need to find what that comprises as a percentage of the total fish population - we have that information with the ratio of the second catch . d

**Annotated formula**

```text
divide(80, divide(2, 50))
```

**Linear formula**

```text
divide(n2,n1)|divide(n0,#0)
```

## 161. mathqa_test_2442

Category: general | Source: test.json, index 2442

a soccer store typically sells replica jerseys at a discount of 30 percent to 50 percent off list price . during the annual summer sale , everything in the store is an additional 20 percent off the original list price . if a replica jersey ' s list price is $ 80 , approximately what w percent of the list price is the lowest possible sale price ?

- **a)** 20
- **b)** 25
- **c)** 30
- **d)** 40
- **e)** 50

**Answer: d) 40**

**Original rationale**

"let the list price be 2 x for min sale price , the first discount given should be 50 % , 2 x becomes x here now , during summer sale additional 20 % off is given ie sale price becomes 0.8 x it is given lise price is $ 80 = > 2 x = 80 = > x = 40 and 0.8 x = 32 so lowest sale price is 32 , which w is 40 % of 80 hence , d is the answer"

**Annotated formula**

```text
divide(80, const_2)
```

**Linear formula**

```text
divide(n3,const_2)|
```

## 162. mathqa_test_2453

Category: gain | Source: test.json, index 2453

a fruit seller had some oranges . he sells 40 % oranges and still has 600 oranges . how many oranges he had originally ?

- **a)** 700
- **b)** 710
- **c)** 1000
- **d)** 730
- **e)** 740

**Answer: c) 1000**

**Original rationale**

"60 % of oranges = 600 100 % of oranges = ( 600 × 100 ) / 6 = 1000 total oranges = 1000 answer : c"

**Annotated formula**

```text
add(600, multiply(600, divide(40, const_100)))
```

**Linear formula**

```text
divide(n0,const_100)|multiply(n1,#0)|add(n1,#1)|
```

## 163. mathqa_test_2465

Category: general | Source: test.json, index 2465

a man saves a certain portion of his income during a year and spends the remaining portion on his personal expenses . next year his income increases by 40 % but his savings increase by 100 % . if his total expenditure in 2 years is double his expenditure in 1 st year , what % age of his income in the first year did he save ?

- **a)** 45 %
- **b)** 40 %
- **c)** 25 %
- **d)** 28 %
- **e)** 33.33 %

**Answer: b) 40 %**

**Original rationale**

i year best is to give a number to his income , say 100 . . and let saving be x . . so expenditure = 100 - x next year - income = 140 savings = 2 x expenditure = 140 - 2 x . . now 140 - 2 x + 100 - x = 2 ( 100 - x ) . . . 240 - 3 x = 200 - 2 x . . . . . . . . . . . . . . . . x = 40 . . . saving % = 40 / 100 * 100 = 40 % answer : b

**Annotated formula**

```text
multiply(divide(subtract(add(add(100, 40), 100), multiply(2, 100)), const_100), const_100)
```

**Linear formula**

```text
add(n0,n1)|multiply(n1,n2)|add(n1,#0)|subtract(#2,#1)|divide(#3,const_100)|multiply(#4,const_100)
```

## 164. mathqa_test_2472

Category: other | Source: test.json, index 2472

the probability that event a occurs is 0.4 , and the probability that events a and b both occur is 0.45 . if the probability that either event a or event b occurs is 0.6 , what is the probability that event b will occur ?

- **a)** 0.05
- **b)** 0.15
- **c)** 0.45
- **d)** 0.5
- **e)** 0.55

**Answer: e) 0.55**

**Original rationale**

"p ( a or b ) = p ( a ) + p ( b ) - p ( a n b ) 0.6 = 0.4 + p ( b ) - 0.45 p ( b ) = 0.55 ans : e"

**Annotated formula**

```text
subtract(add(0.6, 0.45), 0.4)
```

**Linear formula**

```text
add(n1,n2)|subtract(#0,n0)|
```

## 165. mathqa_test_2484

Category: general | Source: test.json, index 2484

what is the range of all the roots of | x ^ 2 - 3 | = x ?

- **a)** 4
- **b)** 3
- **c)** 2
- **d)** 1
- **e)** 0

**Answer: c) 2**

**Original rationale**

"we get 2 quadratic equations here . . 1 ) x ^ 2 - x - 3 = 0 . . . . . . . roots 2 , - 1 2 ) x ^ 2 + x - 3 = 0 . . . . . . . . roots - 2 , 1 inserting each root in given equation , it can be seen that - 1 and - 2 do not satisfy the equations . so value of x for given equation . . . . x = 3 or x = 1 i guess range is 3 - 1 = 2 c"

**Annotated formula**

```text
sqrt(3)
```

**Linear formula**

```text
sqrt(n1)|
```

## 166. mathqa_test_2494

Category: physics | Source: test.json, index 2494

a boy goes to his school from his house at a speed of 3 km / hr and return at a speed of 2 km / hr . if he takes 5 hours in going and coming , the distance between his house and school is ?

- **a)** 5 km
- **b)** 6 km
- **c)** 10 km
- **d)** 12 km
- **e)** 8 km

**Answer: b) 6 km**

**Original rationale**

average speed = 2 * 3 * 2 / 3 + 2 = 12 / 5 km / hr distance traveled = 12 / 5 * 5 = 12 km distance between house and school = 12 / 2 = 6 km answer is b

**Annotated formula**

```text
multiply(divide(5, add(divide(3, 2), const_1)), 3)
```

**Linear formula**

```text
divide(n0,n1)|add(#0,const_1)|divide(n2,#1)|multiply(n0,#2)
```

## 167. mathqa_test_2495

Category: physics | Source: test.json, index 2495

how many seconds will a 600 meter long train take to cross a man walking with a speed of 3 km / hr in the direction of the moving train if the speed of the train is 63 km / hr ?

- **a)** 700
- **b)** 288
- **c)** 500
- **d)** 277
- **e)** 121

**Answer: a) 700**

**Original rationale**

let length of tunnel is x meter distance = 600 + x meter time = 1 minute = 60 seconds speed = 78 km / hr = 78 * 5 / 18 m / s = 65 / 3 m / s distance = speed * time 600 + x = ( 65 / 3 ) * 60 600 + x = 20 * 65 = 1300 x = 1300 - 600 = 700 meters answer : a

**Annotated formula**

```text
multiply(multiply(subtract(divide(600, multiply(subtract(63, 3), const_0_2778)), const_1), const_10), const_2)
```

**Linear formula**

```text
subtract(n2,n1)|multiply(#0,const_0_2778)|divide(n0,#1)|subtract(#2,const_1)|multiply(#3,const_10)|multiply(#4,const_2)
```

## 168. mathqa_test_2533

Category: geometry | Source: test.json, index 2533

if o is the center of the circle in the figure above and the area of the unshaded sector is 5 , what is the area of the shaded region ?

- **a)** 25 / √ π
- **b)** 30 / √ π
- **c)** 20
- **d)** 25
- **e)** 30

**Answer: d) 25**

**Original rationale**

60 / 360 = 1 / 6 1 / 6 of total area = 5 5 / 6 of total area = 5 * 5 = 25 answer : d

**Annotated formula**

```text
power(5, const_2)
```

**Linear formula**

```text
power(n0,const_2)
```

## 169. mathqa_test_2561

Category: general | Source: test.json, index 2561

if y > 0 , ( 10 y ) / 20 + ( 3 y ) / 10 is what percent of y ?

- **a)** 40 %
- **b)** 50 %
- **c)** 60 %
- **d)** 70 %
- **e)** 80 %

**Answer: e) 80 %**

**Original rationale**

"can be reduced to y / 2 + 3 y / 10 = 4 y / 5 = 80 % e"

**Annotated formula**

```text
multiply(const_100, add(divide(10, 20), divide(3, 10)))
```

**Linear formula**

```text
divide(n1,n2)|divide(n3,n4)|add(#0,#1)|multiply(#2,const_100)|
```

## 170. mathqa_test_2570

Category: physics | Source: test.json, index 2570

the distance between 2 cities a and b is 1000 km . a train starts from a at 12 p . m . and travels towards b at 100 km / hr . another starts from b at 1 p . m . and travels towards a at 150 km / hr . at what time do they meet ?

- **a)** 11 am .
- **b)** 12 p . m .
- **c)** 5 pm .
- **d)** 2 p . m .
- **e)** 1 p . m .

**Answer: c) 5 pm .**

**Original rationale**

"suppose they meet x hrs after 12 p . m . distance moved by first in x hrs + distance moved by second in ( x - 1 ) hrs = 1000 100 x + 150 ( x - 1 ) = 1000 x = 4.60 = 5 hrs they meet at 10 + 5 = 5 p . m . answer is c"

**Annotated formula**

```text
add(divide(add(2, 1), add(12, 1)), 1000)
```

**Linear formula**

```text
add(n0,n4)|add(n2,n4)|divide(#0,#1)|add(n1,#2)|
```

## 171. mathqa_test_2574

Category: gain | Source: test.json, index 2574

a reduction of 40 % in the price of oil enables a house wife to obtain 5 kgs more for rs . 800 , what is the reduced price for kg ?

- **a)** 80
- **b)** 72
- **c)** 64
- **d)** 56
- **e)** 48

**Answer: c) 64**

**Original rationale**

"800 * ( 40 / 100 ) = 320 - - - - 5 ? - - - - 1 = > rs . 64 answer : c"

**Annotated formula**

```text
divide(divide(multiply(800, 40), const_100), 5)
```

**Linear formula**

```text
multiply(n0,n2)|divide(#0,const_100)|divide(#1,n1)|
```

## 172. mathqa_test_2600

Category: geometry | Source: test.json, index 2600

a rectangular grass field is 70 m * 55 m , it has a path of 2.5 m wide all round it on the outside . find the area of the path and the cost of constructing it at rs . 2 per sq m ?

- **a)** s . 1350
- **b)** s . 1300
- **c)** s . 1328
- **d)** s . 1397
- **e)** s . 1927

**Answer: b) s . 1300**

**Original rationale**

"area = ( l + b + 2 d ) 2 d = ( 70 + 55 + 2.5 * 2 ) 2 * 2.5 = > 650 650 * 2 = rs . 1300 answer : b"

**Annotated formula**

```text
multiply(subtract(rectangle_area(add(70, multiply(2.5, 2)), add(55, multiply(2.5, 2))), rectangle_area(70, 55)), 2)
```

**Linear formula**

```text
multiply(n2,n3)|rectangle_area(n0,n1)|add(n0,#0)|add(n1,#0)|rectangle_area(#2,#3)|subtract(#4,#1)|multiply(n3,#5)|
```

## 173. mathqa_test_2603

Category: physics | Source: test.json, index 2603

one pipe can fill a tank three times as fast as another pipe . if together the two pipes can fill the tank in 36 minutes , then the slower pipe alone will be able to fill the tank in ?

- **a)** 144 min
- **b)** 250 min
- **c)** 196 min
- **d)** 100 min
- **e)** 112 min

**Answer: a) 144 min**

**Original rationale**

"let the slower pipe alone fill the tank in x minutes then , faster pipe will fill it in x / 3 minutes 1 / x + 3 / x = 1 / 36 4 / x = 1 / 36 x = 144 min answer is a"

**Annotated formula**

```text
multiply(add(const_1, const_4), 36)
```

**Linear formula**

```text
add(const_1,const_4)|multiply(n0,#0)|
```

## 174. mathqa_test_2617

Category: geometry | Source: test.json, index 2617

the volumes of two cubes are in the ratio 27 : 125 , what shall be the ratio of their surface areas ?

- **a)** 6 : 25
- **b)** 3 : 5
- **c)** 9 : 25
- **d)** 16 : 25
- **e)** 19 : 25

**Answer: c) 9 : 25**

**Original rationale**

a 13 : a 23 = 27 : 125 a 1 : a 2 = 3 : 5 6 a 12 : 6 a 22 a 12 : a 22 = 9 : 25 answer : c

**Annotated formula**

```text
divide(surface_cube(divide(divide(27, const_3), const_3)), surface_cube(divide(125, divide(125, add(const_4, const_1)))))
```

**Linear formula**

```text
add(const_1,const_4)|divide(n0,const_3)|divide(#1,const_3)|divide(n1,#0)|divide(n1,#3)|surface_cube(#2)|surface_cube(#4)|divide(#5,#6)
```

## 175. mathqa_test_2619

Category: other | Source: test.json, index 2619

bag contains 7 green and 8 white balls . if two balls are drawn simultaneously , the probability that both are of the same colour is - .

- **a)** 7 / 15
- **b)** 2 / 8
- **c)** 7 / 11
- **d)** 13 / 5
- **e)** 87

**Answer: a) 7 / 15**

**Original rationale**

explanation : drawing two balls of same color from seven green balls can be done in â  · c â ‚ ‚ ways . similarly from eight white balls two can be drawn in â  ¸ c â ‚ ‚ ways . p = â  · c â ‚ ‚ / â ¹ â  µ c â ‚ ‚ + â  ¸ c â ‚ ‚ / â ¹ â  µ c â ‚ ‚ = 7 / 15 a

**Annotated formula**

```text
divide(add(divide(factorial(7), multiply(factorial(subtract(7, const_2)), factorial(const_2))), divide(factorial(8), multiply(factorial(subtract(8, const_2)), factorial(const_2)))), divide(factorial(add(7, 8)), multiply(factorial(subtract(add(7, 8), const_2)), factorial(const_2))))
```

**Linear formula**

```text
add(n0,n1)|factorial(n0)|factorial(const_2)|factorial(n1)|subtract(n0,const_2)|subtract(n1,const_2)|factorial(#4)|factorial(#5)|factorial(#0)|subtract(#0,const_2)|factorial(#9)|multiply(#6,#2)|multiply(#7,#2)|divide(#1,#11)|divide(#3,#12)|multiply(#10,#2)|add(#13,#14)|divide(#8,#15)|divide(#16,#17)
```

## 176. mathqa_test_2621

Category: other | Source: test.json, index 2621

a marketing survey of anytown found that the ratio of trucks to sedans to motorcycles was 3 : 7 : 2 , respectively . given that there are 11,900 sedans in anytown , how many motorcycles are there ?

- **a)** 1260
- **b)** 2100
- **c)** 3400
- **d)** 4200
- **e)** 5200

**Answer: c) 3400**

**Original rationale**

"let the total number of trucks = 3 x total number of sedans = 7 x total number of motorcycles = 2 x total number of sedans = 11900 = > 7 x = 11900 = > x = 1700 total number of motorcycles = 2 x = 2 * 1700 = 3400 answer c"

**Annotated formula**

```text
multiply(divide(add(multiply(multiply(3, 3), const_1000), const_100), 7), 2)
```

**Linear formula**

```text
multiply(n0,n0)|multiply(#0,const_1000)|add(#1,const_100)|divide(#2,n1)|multiply(n2,#3)|
```

## 177. mathqa_test_2625

Category: general | Source: test.json, index 2625

subtracting 30 from a number , the remainder is one fourth of the number . find the number ?

- **a)** 29
- **b)** 88
- **c)** 40
- **d)** 28
- **e)** 27

**Answer: c) 40**

**Original rationale**

explanation : 3 / 4 x = 30 = > x = 40 answer : c

**Annotated formula**

```text
divide(30, subtract(const_1, divide(const_1, const_4)))
```

**Linear formula**

```text
divide(const_1,const_4)|subtract(const_1,#0)|divide(n0,#1)
```

## 178. mathqa_test_2633

Category: probability | Source: test.json, index 2633

how many cubes of 8 cm edge can be cut out of a cube of 16 cm edge

- **a)** 36
- **b)** 2
- **c)** 8
- **d)** 48
- **e)** none of these

**Answer: c) 8**

**Original rationale**

"explanation : number of cubes = ( 16 x 16 x 16 ) / ( 8 x 8 x 8 ) = 8 answer : c"

**Annotated formula**

```text
divide(volume_cube(16), volume_cube(divide(8, const_100)))
```

**Linear formula**

```text
divide(n0,const_100)|volume_cube(n1)|volume_cube(#0)|divide(#1,#2)|
```

## 179. mathqa_test_2654

Category: general | Source: test.json, index 2654

the number 341 is equal to the sum of the cubes of two integers . what is the product of those integers ?

- **a)** 8
- **b)** 15
- **c)** 21
- **d)** 30
- **e)** 39

**Answer: d) 30**

**Original rationale**

5 ^ 3 + 6 ^ 3 = 341 number is 5 * 6 = 30 d

**Annotated formula**

```text
multiply(floor(power(divide(341, const_2), divide(const_1, const_3))), power(subtract(341, power(floor(power(divide(341, const_2), divide(const_1, const_3))), const_3)), divide(const_1, const_3)))
```

**Linear formula**

```text
divide(n0,const_2)|divide(const_1,const_3)|power(#0,#1)|floor(#2)|power(#3,const_3)|subtract(n0,#4)|power(#5,#1)|multiply(#3,#6)
```

## 180. mathqa_test_2661

Category: general | Source: test.json, index 2661

a man covers a certain distance q in a train . if the train moved 4 km / hr faster , it would take 30 min less . if it moved 2 km / hr slower , it would take 20 mins more . find the distance ?

- **a)** 200 km
- **b)** 50 km
- **c)** 20 km
- **d)** 60 km
- **e)** 80 km

**Answer: d) 60 km**

**Original rationale**

not really . when you solve the 2 equation above , you get , 6 t - 4 / 3 = 5 r / 6 from simplifying equation 1 4 t - 2 = r / 2 from simplifying equation 2 you can now multiply equation 2 by 5 to get 5 ( 4 t - 2 = r / 2 ) = 20 t - 10 = 5 r / 2 and then subtract this new equation from equation 1 to get t = 3 , followed by r = 20 to give you distance q = r * t = 20 * 3 = 60 km . d

**Annotated formula**

```text
multiply(divide(subtract(multiply(4, 2), 4), const_2), 30)
```

**Linear formula**

```text
multiply(n0,n2)|subtract(#0,n0)|divide(#1,const_2)|multiply(n1,#2)
```

## 181. mathqa_test_2684

Category: physics | Source: test.json, index 2684

two trains are moving in the same direction at 72 kmph and 36 kmph . the faster train crosses a man in the slower train in 27 seconds . find the length of the faster train ?

- **a)** 270 m
- **b)** 189 m
- **c)** 278 m
- **d)** 279 m
- **e)** 917 m

**Answer: a) 270 m**

**Original rationale**

"relative speed = ( 72 - 36 ) * 5 / 18 = 2 * 5 = 10 mps . distance covered in 27 sec = 27 * 10 = 270 m . the length of the faster train = 270 m . answer : a"

**Annotated formula**

```text
multiply(divide(subtract(72, 36), const_3_6), 27)
```

**Linear formula**

```text
subtract(n0,n1)|divide(#0,const_3_6)|multiply(n2,#1)|
```

## 182. mathqa_test_2702

Category: general | Source: test.json, index 2702

a soccer store typically sells replica jerseys at a discount of 30 percent to 50 percent off list price . during the annual summer sale , everything in the store is an additional 20 percent off the original list price . if a replica jersey ' s list price is $ 80 , approximately what y percent of the list price is the lowest possible sale price ?

- **a)** 20
- **b)** 25
- **c)** 30
- **d)** 40
- **e)** 50

**Answer: d) 40**

**Original rationale**

"let the list price be 2 x for min sale price , the first discount given should be 50 % , 2 x becomes x here now , during summer sale additional 20 % off is given ie sale price becomes 0.8 x it is given lise price is $ 80 = > 2 x = 80 = > x = 40 and 0.8 x = 32 so lowest sale price is 32 , which y is 40 % of 80 hence , d is the answer"

**Annotated formula**

```text
divide(80, const_2)
```

**Linear formula**

```text
divide(n3,const_2)|
```

## 183. mathqa_test_2708

Category: gain | Source: test.json, index 2708

shawn invested one half of his savings in a bond that paid simple interest for 2 years and received $ 400 as interest . he invested the remaining in a bond that paid compound interest , interest being compounded annually , for the same 2 years at the same rate of interest and received $ 605 as interest . what was the value of his total savings before investing in these two bonds ?

- **a)** 3000
- **b)** 5000
- **c)** 2000
- **d)** 4000
- **e)** 6000

**Answer: c) 2000**

**Original rationale**

"so , we know that shawn received 20 % of the amount he invested in a year . we also know that in one year shawn received $ 200 , thus 0.2 x = $ 200 - - > x = $ 1,000 . since , he invested equal sums in his 2 bonds , then his total savings before investing was 2 * $ 1,000 = $ 2,000 . answer : c"

**Annotated formula**

```text
multiply(divide(multiply(divide(400, 2), divide(400, 2)), subtract(605, 400)), 2)
```

**Linear formula**

```text
divide(n1,n0)|subtract(n3,n1)|multiply(#0,#0)|divide(#2,#1)|multiply(n0,#3)|
```

## 184. mathqa_test_2745

Category: general | Source: test.json, index 2745

on sunday , bill ran 4 more miles than he ran on saturday . julia did not run on saturday , but she ran twice the number of miles on sunday that bill ran on sunday . if bill and julia ran a total of 16 miles on saturday and sunday , how many miles did bill run on sunday ?

- **a)** 5
- **b)** 6
- **c)** 7
- **d)** 8
- **e)** 9

**Answer: a) 5**

**Original rationale**

"let bill run x on saturday , so he will run x + 4 on sunday . . julia will run 2 * ( x + 4 ) on sunday . . totai = x + x + 4 + 2 x + 8 = 16 . . 4 x + 12 = 16 . . x = 1 . . ans = x + 4 = 1 + 4 = 5 answer a"

**Annotated formula**

```text
add(divide(subtract(16, add(4, multiply(const_2, 4))), 4), 4)
```

**Linear formula**

```text
multiply(n0,const_2)|add(n0,#0)|subtract(n1,#1)|divide(#2,n0)|add(n0,#3)|
```

## 185. mathqa_test_2771

Category: physics | Source: test.json, index 2771

a train is 360 meter long is running at a speed of 45 km / hour . in what time will it pass a bridge of 240 meter length ?

- **a)** 65 seconds
- **b)** 46 seconds
- **c)** 40 seconds
- **d)** 97 seconds
- **e)** 48 seconds

**Answer: e) 48 seconds**

**Original rationale**

"speed = 45 km / hr = 45 * ( 5 / 18 ) m / sec = 25 / 2 m / sec total distance = 360 + 240 = 600 meter time = distance / speed = 600 * ( 2 / 25 ) = 48 seconds answer : e"

**Annotated formula**

```text
divide(add(360, 240), divide(multiply(45, const_1000), const_3600))
```

**Linear formula**

```text
add(n0,n2)|multiply(n1,const_1000)|divide(#1,const_3600)|divide(#0,#2)|
```

## 186. mathqa_test_2786

Category: general | Source: test.json, index 2786

what is the unit digit in 7105 ?

- **a)** 1
- **b)** 5
- **c)** 7
- **d)** 9
- **e)** 11

**Answer: c) 7**

**Original rationale**

"unit digit in 7105 = unit digit in [ ( 74 ) 26 * 7 ] but , unit digit in ( 74 ) 26 = 1 unit digit in 7105 = ( 1 * 7 ) = 7 answer : c"

**Annotated formula**

```text
circle_area(divide(7105, multiply(const_2, const_pi)))
```

**Linear formula**

```text
multiply(const_2,const_pi)|divide(n0,#0)|circle_area(#1)|
```

## 187. mathqa_test_2787

Category: other | Source: test.json, index 2787

of the 55 cars on a car lot , 40 have air - conditioning , 25 have power windows , and 12 have both air - conditioning and power windows . how many of the cars on the lot have neither air - conditioning nor power windows ?

- **a)** 15
- **b)** 8
- **c)** 10
- **d)** 2
- **e)** 18

**Answer: d) 2**

**Original rationale**

total - neither = all air conditioning + all power windows - both or 55 - neither = 40 + 25 - 12 = 53 . = > neither = 2 , hence d . answer : d

**Annotated formula**

```text
subtract(55, subtract(add(40, 25), 12))
```

**Linear formula**

```text
add(n1,n2)|subtract(#0,n3)|subtract(n0,#1)
```

## 188. mathqa_test_2792

Category: general | Source: test.json, index 2792

if n is a positive integer and n ^ 2 is divisible by 200 , then what is the largest positive integer that must divide n ?

- **a)** 10
- **b)** 15
- **c)** 20
- **d)** 36
- **e)** 50

**Answer: c) 20**

**Original rationale**

200 = 2 ^ 3 * 5 ^ 2 if 200 divides n ^ 2 , then n must be divisible by 2 ^ 2 * 5 = 20 the answer is c .

**Annotated formula**

```text
multiply(sqrt(divide(200, 2)), 2)
```

**Linear formula**

```text
divide(n1,n0)|sqrt(#0)|multiply(n0,#1)
```

## 189. mathqa_test_2799

Category: general | Source: test.json, index 2799

a batsman makes a score of 76 runs in the 17 th inning and thus increases his average by 3 . find his average after 17 th inning .

- **a)** 36
- **b)** 28
- **c)** 42
- **d)** 45
- **e)** none of the above

**Answer: b) 28**

**Original rationale**

"let the average after 17 th inning = x . then , average after 16 th inning = ( x – 3 ) . ∴ 16 ( x – 3 ) + 76 = 17 x or x = ( 76 – 48 ) = 28 . answer b"

**Annotated formula**

```text
add(subtract(76, multiply(17, 3)), 3)
```

**Linear formula**

```text
multiply(n1,n2)|subtract(n0,#0)|add(n2,#1)|
```

## 190. mathqa_test_2804

Category: general | Source: test.json, index 2804

if x is equal to the sum of the integers from 40 to 50 , inclusive , and y is the number of even integers from 40 to 50 , inclusive , what is the value of x + y ?

- **a)** 171
- **b)** 281
- **c)** 391
- **d)** 501
- **e)** 613

**Answer: d) 501**

**Original rationale**

"sum s = n / 2 { 2 a + ( n - 1 ) d } = 11 / 2 { 2 * 40 + ( 11 - 1 ) * 1 } = 11 * 45 = 495 = x number of even number = ( 50 - 40 ) / 2 + 1 = 6 = y x + y = 495 + 6 = 501 d"

**Annotated formula**

```text
add(multiply(divide(add(40, 50), const_2), add(subtract(50, 40), const_1)), add(divide(subtract(50, 40), const_2), const_1))
```

**Linear formula**

```text
add(n0,n1)|subtract(n1,n0)|add(#1,const_1)|divide(#1,const_2)|divide(#0,const_2)|add(#3,const_1)|multiply(#2,#4)|add(#5,#6)|
```

## 191. mathqa_test_2818

Category: other | Source: test.json, index 2818

two numbers are in the ratio 3 : 5 . if 9 be subtracted from each , they are in the ratio of 5 : 2 . the first number is :

- **a)** a ) 3
- **b)** b ) 98
- **c)** c ) 34
- **d)** d ) 35
- **e)** e ) 62

**Answer: a) a ) 3**

**Original rationale**

"( 3 x - 9 ) : ( 5 x - 9 ) = 5 : 2 x = 1 = > 3 x = 3 answer : a"

**Annotated formula**

```text
add(multiply(3, divide(9, multiply(3, 5))), multiply(5, divide(9, multiply(3, 5))))
```

**Linear formula**

```text
multiply(n0,n1)|divide(n2,#0)|multiply(n0,#1)|multiply(n1,#1)|add(#2,#3)|
```

## 192. mathqa_test_2859

Category: general | Source: test.json, index 2859

the original price of a suit is $ 200 . the price increased 20 % , and after this increase , the store published a 20 % off coupon for a one - day sale . given that the consumers who used the coupon on sale day were getting 20 % off the increased price , how much did these consumers pay for the suit ?

- **a)** $ 192
- **b)** $ 198
- **c)** $ 200
- **d)** $ 208
- **e)** $ 216

**Answer: a) $ 192**

**Original rationale**

"0.8 * ( 1.2 * 200 ) = $ 192 the answer is a ."

**Annotated formula**

```text
subtract(add(200, divide(multiply(200, 20), const_100)), divide(multiply(add(200, divide(multiply(200, 20), const_100)), 20), const_100))
```

**Linear formula**

```text
multiply(n0,n1)|divide(#0,const_100)|add(n0,#1)|multiply(n1,#2)|divide(#3,const_100)|subtract(#2,#4)|
```

## 193. mathqa_test_2872

Category: geometry | Source: test.json, index 2872

the parameter of a square is equal to the perimeter of a rectangle of length 16 cm and breadth 14 cm . find the circumference of a semicircle whose diameter is equal to the side of the square . ( round off your answer to two decimal places

- **a)** 34
- **b)** 35
- **c)** 56
- **d)** 67
- **e)** 23.57

**Answer: e) 23.57**

**Original rationale**

"let the side of the square be a cm . parameter of the rectangle = 2 ( 16 + 14 ) = 60 cm parameter of the square = 60 cm i . e . 4 a = 60 a = 15 diameter of the semicircle = 15 cm circimference of the semicircle = 1 / 2 ( ∏ ) ( 15 ) = 1 / 2 ( 22 / 7 ) ( 15 ) = 330 / 14 = 23.57 cm to two decimal places answer : option e"

**Annotated formula**

```text
divide(circumface(divide(square_edge_by_perimeter(rectangle_perimeter(16, 14)), const_2)), const_2)
```

**Linear formula**

```text
rectangle_perimeter(n0,n1)|square_edge_by_perimeter(#0)|divide(#1,const_2)|circumface(#2)|divide(#3,const_2)|
```

## 194. mathqa_test_2874

Category: physics | Source: test.json, index 2874

x can do a piece of work in 4 hours ; y and z together can do it in 3 hours , while x and z together can do it in 2 hours . how long will y alone take to do it ?

- **a)** 5 hours
- **b)** 10 hours
- **c)** 12 hours
- **d)** 24 hours
- **e)** 15 hours

**Answer: c) 12 hours**

**Original rationale**

x 1 hour ' s work = 1 / 4 ; y + z ' s hour ' s work = 1 / 3 x + y + z ' s 1 hour ' s work = 1 / 4 + 1 / 3 = 7 / 12 y ' s 1 hour ' s work = ( 7 / 12 - 1 / 2 ) = 1 / 12 . y alone will take 12 hours to do the work . c

**Annotated formula**

```text
inverse(subtract(divide(const_1, 3), subtract(divide(const_1, 2), divide(const_1, 4))))
```

**Linear formula**

```text
divide(const_1,n1)|divide(const_1,n2)|divide(const_1,n0)|subtract(#1,#2)|subtract(#0,#3)|inverse(#4)
```

## 195. mathqa_test_2885

Category: general | Source: test.json, index 2885

107 x 107 + 93 x 93 = ?

- **a)** 19578
- **b)** 19418
- **c)** 20098
- **d)** 21908
- **e)** none of them

**Answer: c) 20098**

**Original rationale**

"= ( 107 ) ^ 2 + ( 93 ) ^ 2 = ( 100 + 7 ) ^ 2 + ( 100 - 7 ) ^ 2 = 2 x [ ( 100 ) ^ 2 + 7 ^ 2 ] = 2 [ 10000 + 49 ] = 2 x 10049 = 20098 answer is c"

**Annotated formula**

```text
multiply(107, power(107, 93))
```

**Linear formula**

```text
power(n1,n2)|multiply(n0,#0)|
```

## 196. mathqa_test_2932

Category: general | Source: test.json, index 2932

mark bought a set of 6 flower pots of different sizes at a total cost of $ 8.00 . each pot cost 0.25 more than the next one below it in size . what was the cost , in dollars , of the largest pot ?

- **a)** $ 1.75
- **b)** $ 1.96
- **c)** $ 2.00
- **d)** $ 2.15
- **e)** $ 2.30

**Answer: b) $ 1.96**

**Original rationale**

"this question can be solved with a handful of different algebra approaches ( as has been shown in the various posts ) . since the question asks for the price of the largest pot , and the answers are prices , we can test the answers . we ' re told that there are 6 pots and that each pot costs 25 cents more than the next . the total price of the pots is $ 8.25 . we ' re asked for the price of the largest ( most expensive ) pot . since the total price is $ 8.00 ( a 25 - cent increment ) and the the difference in sequential prices of the pots is 25 cents , the largest pot probably has a price that is a 25 - cent increment . from the answer choices , i would then test answer c first ( since answers b and d are not in 25 - cent increments ) . if . . . . the largest pot = $ 1.958 0.708 0.958 1.208 1.458 1.708 1.958 total = $ 8.00 so this must be the answer . b"

**Annotated formula**

```text
add(divide(subtract(8.00, multiply(divide(multiply(subtract(6, const_1), 6), const_2), 0.25)), 6), multiply(subtract(6, const_1), 0.25))
```

**Linear formula**

```text
subtract(n0,const_1)|multiply(n0,#0)|multiply(n2,#0)|divide(#1,const_2)|multiply(n2,#3)|subtract(n1,#4)|divide(#5,n0)|add(#6,#2)|
```

## 197. mathqa_test_2940

Category: general | Source: test.json, index 2940

32.32 / 2000 is equal to :

- **a)** 1.012526
- **b)** 0.012625
- **c)** 0.12526
- **d)** 0.01616
- **e)** 0.12725

**Answer: d) 0.01616**

**Original rationale**

"25.25 / 2000 = 2525 / 200000 = 0.01616 answer : d"

**Annotated formula**

```text
divide(32.32, 2000)
```

**Linear formula**

```text
divide(n0,n1)|
```

## 198. mathqa_test_2947

Category: general | Source: test.json, index 2947

anne earned $ 3 an hour baby - sitting , and $ 4 an hour working in the garden . last week she did baby - sitting for 5 hours and garden work for 3 hours . how much more money does she need to buy a game that costs $ 35 ?

- **a)** $ 8
- **b)** $ 12
- **c)** $ 6
- **d)** $ 21
- **e)** $ 10

**Answer: a) $ 8**

**Original rationale**

5 x $ 3 = $ 15 for baby - sitting 3 x $ 4 = $ 12 for garden work $ 15 + $ 12 = $ 27 she has $ 35 - $ 27 = $ 8 more needed to buy the game correct answer a

**Annotated formula**

```text
subtract(35, add(multiply(5, 3), multiply(3, 4)))
```

**Linear formula**

```text
multiply(n0,n2)|multiply(n0,n1)|add(#0,#1)|subtract(n4,#2)
```

## 199. mathqa_test_2952

Category: other | Source: test.json, index 2952

income and expenditure of a person are in the ratio 5 : 4 . if the income of the person is rs . 14000 , then find his savings ?

- **a)** 3600
- **b)** 2800
- **c)** 3608
- **d)** 3602
- **e)** 3603

**Answer: b) 2800**

**Original rationale**

"let the income and the expenditure of the person be rs . 5 x and rs . 4 x respectively . income , 5 x = 14000 = > x = 2800 savings = income - expenditure = 5 x - 4 x = x so , savings = rs . 2800 . answer : b"

**Annotated formula**

```text
subtract(14000, multiply(divide(4, 5), 14000))
```

**Linear formula**

```text
divide(n1,n0)|multiply(n2,#0)|subtract(n2,#1)|
```

## 200. mathqa_test_2957

Category: geometry | Source: test.json, index 2957

if the area of a square with sides of length 3 centimeters is equal to the area of a rectangle with a width of 4 centimeters , what is the length of the rectangle , in centimeters ?

- **a)** 4
- **b)** 8
- **c)** 12
- **d)** 3
- **e)** 18

**Answer: d) 3**

**Original rationale**

"let length of rectangle = l 3 ^ 2 = l * 4 = > l = 9 / 4 = 3 answer d"

**Annotated formula**

```text
divide(power(3, const_2), 4)
```

**Linear formula**

```text
power(n0,const_2)|divide(#0,n1)|
```
