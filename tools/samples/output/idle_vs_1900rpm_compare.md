# Comparison: idle vs 1900rpm

## 170
### record 00

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | changed | 02 | 07 |
| 1 | changed | 31,35,36,37,38,39,3B,3C,3D,3E,3F,40,41,42,43,44,45,46,47,48,49,4A,4B,4C,4D,4E,4F,50,51,52,53,54,55,56,57,59,5E | 66,67,68,69,6A,6B,6C,6D,6E,6F,70,71,72,73,74,75,76,77,78,79,7A,7B,7C,7D,7E,7F,80,81,82,83,84,85,86,87,88,89,8A,8B,8C,8D,8E,8F,90,91,92,95,97,99 |
| 2 | constant | 04 | 04 |
| 3 | changed | 15 | 0C |
| 4 | variable | 2F,3E,3F,41,46,47,49,4A,4F,50,52,55,56,58,59,5A,5B,5C,5F,60,61,62,63,64,65,67,69,6A,6B,6C,6D,6F,71,72,73,74,75,76,77,78,79,7A,7B,7C,7D,7E,7F,80,81,82,83,84,86,87,88,89,8A,8B,8C,8D,8E,8F,90,91,92,93,94,95,96,97,98,99,9A,9B,9C,9D,9E,9F,A0,A1,A2,A3,A4,A5,A6,A7,A8,A9,AA,AB,AC,AD,AE,AF,B0,B1,B2,B3,B4,B5,B6,B7,B8,B9,BA,BB,BC,BE,BF,C0,C1,C2,C5,C6,C7,C8,C9,CA,CB,CC,CD,CE,CF,D0,D1,D3,D5,D6,D7,D8,DB,E4,E7,EA | 1B,25,27,28,2A,2C,2D,2F,30,31,32,33,34,35,36,37,38,39,3A,3B,3C,3D,3E,3F,40,41,42,43,44,45,46,47,48,49,4A,4B,4C,4D,4E,4F,50,51,52,53,54,55,56,57,58,59,5A,5B,5C,5D,5E,5F,60,61,63,64,6B |
| 5 | constant | FF | FF |
| 6 | constant | FF | FF |

### record 01

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | changed | 01 | 02 |
| 1 | variable | 46,48,49,4A,4B,4C,4D,4E,4F,50,51,52,53,54,55,56,57,58,59,5A,5B,5C,5D,5E,5F,60,61,62 | 52,53,54,55,56,57,58,59,5A,5B,5C,5D,5E |
| 2 | constant | 73 | 73 |
| 3 | constant | A0 | A0 |
| 4 | changed | 11 | 1A |
| 5 | variable | 25,28,2B,34,37,38,39,3A,3C,3E,3F,40,41,42,43,44,45,46,47,48,49,4A,4D,4E,4F,50,51,53,54,55,56,57,58,59,5A,5B,5C,5D,5E,5F,60,61,62,63,64,65,66,67,68,69,6A,6B,6C,6D,6E,6F,70,71,72,73,74,75,76,77,78,79,7A,7B,7C,7D,7E,7F,80,81,82,83,84,85,86,87,88,89,8B,8C,8D,8E,8F,90,91,92,93,94,95,96,97,98,99,9A,9B,9C,9D,9E,A0,A2,A3,A4,A5,A6,A8,AA,AB,AC,AD,AE,AF,B0,B3,B4,B5,B6,B7,B9,BA,BD,BF,C0,C5,C6,C8,C9,CE,D0,D1,E0 | A4,AB,AC,AE,AF,B0,B1,B2,B3,B4,B5,B6,B7,B8,B9,BA,BB,BC,BD,BE,BF,C0,C1,C2,C3,C4,C5,C6,C7,C8,C9,CA,CB,CC,CD,CE,CF,D0,D1,D2,D3,D4,D5,D6,D7,D8,D9,DA,DB,DC,DD,DE,DF,E0,E2,E3,E5,E7,E8,EA,F4 |
| 6 | constant | 00 | 00 |

### record 02

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 00 | 00 |
| 1 | constant | 09 | 09 |
| 2 | constant | 00 | 00 |
| 3 | constant | 00 | 00 |
| 4 | constant | 00 | 00 |
| 5 | constant | 00 | 00 |
| 6 | constant | 00 | 00 |

### record 03

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | variable | 04,05 | 04,05 |
| 1 | variable | 15,2E,48,61,62,7B,95,AE,C8,E2,FB | 15,2E,48,61,95,AE,C8,E2,FB |
| 2 | constant | 00 | 00 |
| 3 | constant | 00 | 00 |
| 4 | constant | 00 | 00 |
| 5 | constant | FF | FF |
| 6 | constant | FF | FF |

### record 04

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 00 | 00 |
| 1 | constant | 00 | 00 |
| 2 | constant | 00 | 00 |
| 3 | constant | 00 | 00 |
| 4 | constant | 00 | 00 |
| 5 | constant | 00 | 00 |
| 6 | constant | 00 | 00 |

### record 05

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 00 | 00 |
| 1 | constant | 00 | 00 |
| 2 | constant | 00 | 00 |
| 3 | constant | 00 | 00 |
| 4 | constant | 00 | 00 |
| 5 | constant | 00 | 00 |
| 6 | constant | 00 | 00 |

### record 06

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 00 | 00 |
| 1 | constant | 00 | 00 |
| 2 | constant | 00 | 00 |
| 3 | constant | 00 | 00 |
| 4 | constant | 00 | 00 |
| 5 | constant | 00 | 00 |
| 6 | constant | 00 | 00 |

### record FF

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 00 | 00 |
| 1 | constant | 00 | 00 |
| 2 | constant | 00 | 00 |
| 3 | constant | 00 | 00 |
| 4 | constant | 00 | 00 |
| 5 | constant | 00 | 00 |
| 6 | constant | 00 | 00 |

## 1A0
### record 00

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 03 | 03 |
| 1 | changed | 01 | 02 |
| 2 | changed | 01 | 00 |
| 3 | constant | 00 | 00 |
| 4 | constant | 00 | 00 |
| 5 | constant | 00 | 00 |
| 6 | constant | 00 | 00 |

### record 01

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 80 | 80 |
| 1 | constant | 00 | 00 |
| 2 | constant | 00 | 00 |
| 3 | constant | 00 | 00 |
| 4 | constant | 00 | 00 |
| 5 | constant | 00 | 00 |
| 6 | constant | 00 | 00 |

### record 02

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 00 | 00 |
| 1 | constant | 00 | 00 |
| 2 | changed | 92 | 93 |
| 3 | changed | FD,FE | 04 |
| 4 | constant | 00 | 00 |
| 5 | constant | 00 | 00 |
| 6 | constant | 00 | 00 |

### record 03

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 00 | 00 |
| 1 | constant | 00 | 00 |
| 2 | constant | 00 | 00 |
| 3 | constant | 00 | 00 |
| 4 | constant | 00 | 00 |
| 5 | constant | 00 | 00 |
| 6 | constant | 00 | 00 |

### record 04

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | variable | 0E,12,13 | 0E,12,13 |
| 1 | variable | 07,17,1F,30,38,49,51,62,7B,E5,F8,FE | 17,30,38,49,51,62,6A,7B,83,94,9C,AD,E7,FE |
| 2 | constant | 00 | 00 |
| 3 | constant | 00 | 00 |
| 4 | constant | 00 | 00 |
| 5 | constant | 00 | 00 |
| 6 | constant | 00 | 00 |

### record 05

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 00 | 00 |
| 1 | constant | 00 | 00 |
| 2 | changed | 87,88 | A1,A2,A3,A4,A5 |
| 3 | variable | 01,02,11,1B,25,28,31,37,38,3D,3E,46,64,7A,98,9C,9F,B2,BF,C3,C9,D4,DA,E0,E2,E6,E9,EC,F0,F2,F5,F8,F9,FD,FE | 13,16,18,19,20,25,26,4B,4D,4E,53,57,5A,5D,5E,64,83,86,8A,8E,9E,A1,A6,A9,AC,B1,BA,BB,CC,DB,DC,E3,E5 |
| 4 | constant | 00 | 00 |
| 5 | constant | 00 | 00 |
| 6 | constant | 00 | 00 |

### record 06

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 00 | 00 |
| 1 | constant | 00 | 00 |
| 2 | constant | 00 | 00 |
| 3 | constant | 00 | 00 |
| 4 | constant | 00 | 00 |
| 5 | constant | 00 | 00 |
| 6 | constant | 00 | 00 |

### record 07

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 00 | 00 |
| 1 | changed | 3F,40 | 42 |
| 2 | constant | 00 | 00 |
| 3 | constant | 00 | 00 |
| 4 | changed | 02 | 09 |
| 5 | variable | 3A,49,4F,55,5A,65,67,69,6A,6C,6D,70,7E,86,89,8B,8F,90,98,9A,A0,A1,A3,A5,A7,A9,AD,AF,B0,B7,BC,C3,C4,C8,D0,F2 | 7A,81,85,87,88,8B,8F,93,94,98,99,9A,9B,9C,9E,A0,A3,A4,A6,A7,A8,AE,AF,B0,B1,B3,BB,BD |
| 6 | constant | 00 | 00 |

### record 08

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 00 | 00 |
| 1 | constant | 00 | 00 |
| 2 | constant | 00 | 00 |
| 3 | constant | 00 | 00 |
| 4 | constant | 00 | 00 |
| 5 | constant | 00 | 00 |
| 6 | constant | 00 | 00 |

### record 09

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 27 | 27 |
| 1 | constant | 0F | 0F |
| 2 | constant | DD | DD |
| 3 | variable | 36 | 36,37 |
| 4 | variable | 0E,29,44,5F,7A,95,B0,CB,E6 | 01,1C,29,37,44,5F,7A,95,B0,CB,E6 |
| 5 | constant | 00 | 00 |
| 6 | constant | 00 | 00 |

### record 0A

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 50 | 50 |
| 1 | constant | 32 | 32 |
| 2 | constant | 27 | 27 |
| 3 | constant | 10 | 10 |
| 4 | constant | 14 | 14 |
| 5 | constant | 82 | 82 |
| 6 | constant | 06 | 06 |

### record 0B

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | variable | 01 | 00,01 |
| 1 | variable | 02,03,04,05,06,07,08,09,0A,0B,0C,10,11,13,14,15 | 02,03,04,05,06,07,08,09,0A,0B,0D,0E,10,83,BF,C3,FE,FF |
| 2 | constant | 00 | 00 |
| 3 | variable | F7,F8 | F8 |
| 4 | constant | 00 | 00 |
| 5 | constant | 00 | 00 |
| 6 | constant | 0B | 0B |

### record 0C

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 00 | 00 |
| 1 | constant | 00 | 00 |
| 2 | constant | 00 | 00 |
| 3 | constant | 00 | 00 |
| 4 | constant | 00 | 00 |
| 5 | constant | 00 | 00 |
| 6 | constant | 00 | 00 |

### record FF

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 00 | 00 |
| 1 | constant | 00 | 00 |
| 2 | constant | 00 | 00 |
| 3 | constant | 00 | 00 |
| 4 | constant | 00 | 00 |
| 5 | constant | 00 | 00 |
| 6 | constant | 00 | 00 |

## 1E0
### record 00

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 00 | 00 |
| 1 | constant | 00 | 00 |
| 2 | changed | 92 | 93 |
| 3 | changed | FD | 04 |
| 4 | constant | 00 | 00 |
| 5 | constant | 00 | 00 |
| 6 | constant | 00 | 00 |

### record 01

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 00 | 00 |
| 1 | constant | 00 | 00 |
| 2 | constant | 1F | 1F |
| 3 | changed | 86 | 87 |
| 4 | constant | 00 | 00 |
| 5 | constant | 00 | 00 |
| 6 | constant | 00 | 00 |

### record 02

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 00 | 00 |
| 1 | constant | 00 | 00 |
| 2 | constant | 2B | 2B |
| 3 | changed | 48 | 4A |
| 4 | constant | 00 | 00 |
| 5 | constant | 0F | 0F |
| 6 | constant | 00 | 00 |

### record 03

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 00 | 00 |
| 1 | constant | 00 | 00 |
| 2 | constant | 3B | 3B |
| 3 | changed | 4E | 52 |
| 4 | constant | 0F | 0F |
| 5 | constant | 1E | 1E |
| 6 | constant | 00 | 00 |

### record 04

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 00 | 00 |
| 1 | constant | 00 | 00 |
| 2 | constant | 07 | 07 |
| 3 | constant | 36 | 36 |
| 4 | constant | 1E | 1E |
| 5 | constant | 3C | 3C |
| 6 | constant | 00 | 00 |

### record 05

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 00 | 00 |
| 1 | constant | 00 | 00 |
| 2 | constant | 04 | 04 |
| 3 | constant | 6F | 6F |
| 4 | constant | 3C | 3C |
| 5 | constant | 46 | 46 |
| 6 | constant | 00 | 00 |

### record 06

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 00 | 00 |
| 1 | constant | 00 | 00 |
| 2 | constant | 00 | 00 |
| 3 | constant | FF | FF |
| 4 | constant | 46 | 46 |
| 5 | constant | 50 | 50 |
| 6 | constant | 00 | 00 |

### record 07

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 00 | 00 |
| 1 | constant | 00 | 00 |
| 2 | constant | 00 | 00 |
| 3 | constant | 3D | 3D |
| 4 | constant | 50 | 50 |
| 5 | constant | 5A | 5A |
| 6 | constant | 00 | 00 |

### record 08

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 00 | 00 |
| 1 | constant | 00 | 00 |
| 2 | constant | 00 | 00 |
| 3 | constant | 00 | 00 |
| 4 | constant | 5A | 5A |
| 5 | constant | 64 | 64 |
| 6 | constant | 00 | 00 |

### record 09

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 00 | 00 |
| 1 | constant | 00 | 00 |
| 2 | constant | 00 | 00 |
| 3 | constant | 00 | 00 |
| 4 | constant | 6E | 6E |
| 5 | constant | FF | FF |
| 6 | constant | 00 | 00 |

### record 0A

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 01 | 01 |
| 1 | constant | 00 | 00 |
| 2 | constant | 00 | 00 |
| 3 | constant | 00 | 00 |
| 4 | constant | 00 | 00 |
| 5 | constant | 00 | 00 |
| 6 | constant | 00 | 00 |

### record 0B

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 00 | 00 |
| 1 | constant | 00 | 00 |
| 2 | constant | 00 | 00 |
| 3 | constant | 00 | 00 |
| 4 | constant | 00 | 00 |
| 5 | constant | 00 | 00 |
| 6 | constant | 00 | 00 |

### record 0C

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 00 | 00 |
| 1 | constant | 00 | 00 |
| 2 | constant | 00 | 00 |
| 3 | constant | 00 | 00 |
| 4 | constant | 00 | 00 |
| 5 | constant | 00 | 00 |
| 6 | constant | 00 | 00 |

### record 0D

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 00 | 00 |
| 1 | constant | 00 | 00 |
| 2 | constant | 00 | 00 |
| 3 | constant | 00 | 00 |
| 4 | constant | 00 | 00 |
| 5 | constant | 00 | 00 |
| 6 | constant | 00 | 00 |

### record 0E

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 00 | 00 |
| 1 | constant | 00 | 00 |
| 2 | constant | 00 | 00 |
| 3 | constant | 00 | 00 |
| 4 | constant | 00 | 00 |
| 5 | constant | 00 | 00 |
| 6 | constant | 00 | 00 |

### record 0F

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 00 | 00 |
| 1 | constant | 00 | 00 |
| 2 | constant | 00 | 00 |
| 3 | constant | 00 | 00 |
| 4 | constant | 00 | 00 |
| 5 | constant | 00 | 00 |
| 6 | constant | 00 | 00 |

### record 10

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 00 | 00 |
| 1 | constant | 00 | 00 |
| 2 | constant | 00 | 00 |
| 3 | constant | 00 | 00 |
| 4 | constant | 00 | 00 |
| 5 | constant | 00 | 00 |
| 6 | constant | 00 | 00 |

### record 11

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 00 | 00 |
| 1 | constant | 00 | 00 |
| 2 | constant | 00 | 00 |
| 3 | constant | 00 | 00 |
| 4 | constant | 00 | 00 |
| 5 | constant | 00 | 00 |
| 6 | constant | 00 | 00 |

### record 12

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 00 | 00 |
| 1 | constant | 00 | 00 |
| 2 | constant | 00 | 00 |
| 3 | constant | 00 | 00 |
| 4 | constant | 00 | 00 |
| 5 | constant | 00 | 00 |
| 6 | constant | 00 | 00 |

### record 13

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 00 | 00 |
| 1 | constant | 00 | 00 |
| 2 | constant | 00 | 00 |
| 3 | constant | 00 | 00 |
| 4 | constant | 00 | 00 |
| 5 | constant | 00 | 00 |
| 6 | constant | 00 | 00 |

### record 14

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 00 | 00 |
| 1 | constant | 00 | 00 |
| 2 | constant | 00 | 00 |
| 3 | constant | 00 | 00 |
| 4 | constant | 00 | 00 |
| 5 | constant | 00 | 00 |
| 6 | constant | 00 | 00 |

### record 15

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 40 | 40 |
| 1 | constant | 00 | 00 |
| 2 | constant | 00 | 00 |
| 3 | constant | 00 | 00 |
| 4 | constant | 00 | 00 |
| 5 | constant | 00 | 00 |
| 6 | constant | 00 | 00 |

### record 16

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 00 | 00 |
| 1 | constant | 00 | 00 |
| 2 | constant | 00 | 00 |
| 3 | constant | 00 | 00 |
| 4 | constant | 00 | 00 |
| 5 | constant | 00 | 00 |
| 6 | constant | 00 | 00 |

### record 17

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 29 | 29 |
| 1 | constant | 01 | 01 |
| 2 | constant | 0A | 0A |
| 3 | constant | 09 | 09 |
| 4 | constant | 0B | 0B |
| 5 | constant | 00 | 00 |
| 6 | constant | 00 | 00 |

### record FF

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 00 | 00 |
| 1 | constant | 00 | 00 |
| 2 | constant | 00 | 00 |
| 3 | constant | 00 | 00 |
| 4 | constant | 00 | 00 |
| 5 | constant | 00 | 00 |
| 6 | constant | 00 | 00 |

## 1F0
### record 00

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 17 | 17 |
| 1 | constant | 00 | 00 |
| 2 | constant | 02 | 02 |
| 3 | constant | 03 | 03 |
| 4 | constant | 00 | 00 |
| 5 | constant | 00 | 00 |
| 6 | constant | 00 | 00 |

### record 01

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 77 | 77 |
| 1 | constant | 01 | 01 |
| 2 | constant | 00 | 00 |
| 3 | constant | 00 | 00 |
| 4 | constant | 00 | 00 |
| 5 | constant | 00 | 00 |
| 6 | constant | 00 | 00 |

### record FF

| byte | verdict | values in idle | values in 1900rpm |
|---|---|---|---|
| 0 | constant | 17 | 17 |
| 1 | constant | 00 | 00 |
| 2 | constant | 00 | 00 |
| 3 | constant | 03 | 03 |
| 4 | constant | 00 | 00 |
| 5 | constant | 00 | 00 |
| 6 | constant | 00 | 00 |
