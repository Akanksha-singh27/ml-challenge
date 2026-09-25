# Exploration Report
data_dir = dataset

# TRAIN

## TRAIN source1
- rows: 2206821
- columns: ['entity_id', 'business_name', 'business_address', 'country']
- empty `business_name`: 0 (0.00%)
- empty `business_address`: 0 (0.00%)
- empty `country`: 0 (0.00%)
- country value counts:
    'US': 1323633
    'India': 883188
- business_name with non-ASCII chars (possible transliteration): 0 (0.00%)
- most common last tokens in business_name (legal suffix candidates):
    'limited': 521915
    'llc': 355736
    'inc': 238306
    'ltd': 148595
    'llp': 39725
    'corp': 33761
    'group': 32678
    'pc': 25827
    'co': 25178
    'center': 22269
    'associates': 22165
    'p.c': 22040
    'l.l.c': 21843
    'pllc': 20531
    'partners': 19351
    'clinic': 18107
    'care': 16845
    'lp': 16477
    'corporation': 13540
    'company': 12316
- exact duplicate (non-empty) business_name rows: 667592
- addresses with landmark references (near/opposite/behind/...): 101138 (4.58%)
- addresses with a 5-6 digit number (possible ZIP/PIN): 147257 (6.67%)
- addresses with non-ASCII chars: 554 (0.03%)
- sample rows (name | address | country):
    'Pediatric Medicine PLLC' | '4850 20, Otisco, NY' | 'US'
    'Fetech National Twin' | '19034 Woodburn Road, Woodburn, IN' | 'US'
    'General Design Innovations LLC' | '7241 Osage Avenue, Mesa, AZ' | 'US'
    'Construction Ideaz Papers Private Limited' | 'Building No.4/606, Prabhul Cottage Karimbalur, Elakamon, Ayiroor P.O., Thiruvananthapuram, Trivandrum, Kerala' | 'India'
    'Penaloza and Bittle First Inc.' | '4255 Charleswood Avenue, Memphis, TN' | 'US'

## TRAIN source2
- rows: 5034616
- columns: ['entity_id', 'business_name', 'business_address', 'country']
- empty `business_name`: 0 (0.00%)
- empty `business_address`: 168967 (3.36%)
- empty `country`: 0 (0.00%)
- country value counts:
    'US': 3016817
    'India': 2017799
- business_name with non-ASCII chars (possible transliteration): 764608 (15.19%)
- most common last tokens in business_name (legal suffix candidates):
    'limited': 380095
    'llc': 372229
    'ltd': 319650
    'inc': 289013
    'लिमिटेड': 190091
    'center': 133663
    'private': 109874
    'corp': 109097
    'co': 102113
    'services': 90179
    'partners': 84616
    'group': 75033
    'holdings': 57564
    'l.l.c': 50025
    'corporation': 49875
    'llp': 45351
    'service': 41716
    'lp': 39040
    'लि': 35416
    'pvt': 34156
- exact duplicate (non-empty) business_name rows: 632607
- addresses with landmark references (near/opposite/behind/...): 197600 (3.92%)
- addresses with a 5-6 digit number (possible ZIP/PIN): 369140 (7.33%)
- addresses with non-ASCII chars: 478453 (9.50%)
- sample rows (name | address | country):
    'Harbor  Center' | '6309 EVANGELINE TRAIL, AUSTIN, TX' | 'US'
    'STEWARD ACE PREMIER' | '1029 MAPLE HILL RD, LEBANON, TN' | 'US'
    'Klapper and Lott' | '368 VINE STREET, TOOELE, UT' | 'US'
    'EAR NOSE & THROAT CARE' | 'YORK RD, LUTHERVILLE, MD' | 'US'
    'Shield Inrfabuild Private Limited' | '206 FLAT NO. LG 1 KH NO. 514, 516 SHYAM BHAWAN JHANDA COLONY FATEHPUR, DELHI, Delhi' | 'India'

## TRAIN source3
- rows: 5285603
- columns: ['entity_id', 'business_name', 'business_address', 'country']
- empty `business_name`: 0 (0.00%)
- empty `business_address`: 175916 (3.33%)
- empty `country`: 0 (0.00%)
- country value counts:
    'US': 3170056
    'India': 2115547
- business_name with non-ASCII chars (possible transliteration): 606737 (11.48%)
- most common last tokens in business_name (legal suffix candidates):
    'limited': 484402
    'llc': 406439
    'ltd': 339833
    'inc': 303389
    'center': 156721
    'private': 114697
    'corp': 106656
    'लिमिटेड': 106538
    'services': 105211
    'co': 99916
    'partners': 93953
    'group': 77789
    'holdings': 58346
    'llp': 54001
    'service': 49076
    'l.l.c': 46998
    'corporation': 45479
    'lp': 36607
    'pvt': 34400
    'pc': 24062
- exact duplicate (non-empty) business_name rows: 633994
- addresses with landmark references (near/opposite/behind/...): 157318 (2.98%)
- addresses with a 5-6 digit number (possible ZIP/PIN): 385727 (7.30%)
- addresses with non-ASCII chars: 476588 (9.02%)
- sample rows (name | address | country):
    'Dr Apex Pvt Ltd Partners' | '75 Tulshibaugwale Colonysahakarnagar, Pune, MH' | 'India'
    'Shiva  Mines Pvt Ltd' | 'F-17, Sector 22, Noida, Gautam Buddha Nagar, उत्तर प्रदेश' | 'India'
    'Vanguard Métropolitan Sunshine' | '3518-B Crestview Ln, Catoosa, Oklahoma' | 'US'
    'Vanguard Apoge-Inc' | '2150 350, Greencastle, Indiana' | 'US'
    'रियल एग्रो प्राइवेट लिमिटेड' | 'H.no 829 D-225vivek Vihar, Delhi, दिल्ली' | 'India'

## TRAIN ground_truth
- rows: 2206821
- S1 entities with at least one match: 2083574 (94.42%)
- singletons (no match): 123247 (5.58%)
- avg matches per S1 entity (incl. singletons): 3.46
- max matches for a single S1 entity: 11

# TEST

## TEST source1
- rows: 1732544
- columns: ['entity_id', 'business_name', 'business_address', 'country']
- empty `business_name`: 0 (0.00%)
- empty `business_address`: 0 (0.00%)
- empty `country`: 0 (0.00%)
- country value counts:
    'India': 809986
    'US': 663106
    'France': 259452
- business_name with non-ASCII chars (possible transliteration): 40789 (2.35%)
- most common last tokens in business_name (legal suffix candidates):
    'limited': 478456
    'llc': 178364
    'ltd': 134639
    'inc': 119196
    'sarl': 73480
    'sas': 52276
    'llp': 36037
    'corp': 19782
    'co': 19735
    'group': 18713
    'eurl': 16979
    'associates': 12938
    'pc': 12936
    'sa': 12754
    'center': 12471
    'partners': 11628
    'clinic': 11323
    'p.c': 10916
    'sasu': 10721
    'l.l.c': 10696
- exact duplicate (non-empty) business_name rows: 493677
- addresses with landmark references (near/opposite/behind/...): 92421 (5.33%)
- addresses with a 5-6 digit number (possible ZIP/PIN): 75634 (4.37%)
- addresses with non-ASCII chars: 73800 (4.26%)
- sample rows (name | address | country):
    'Coastal Classic Chiron Inc' | 'Broken Arrow, 3621 35th Circle, OK' | 'US'
    'Svn Traders LLP' | 'H.No 143 / B-4 Paschim Vihar, New Delhi, North Delhi, Delhi' | 'India'
    'École primaire de Georges' | '4 Rue de la Constitution, Nantes, Pays de la Loire' | 'France'
    'Hari Energy Private Limited' | '4C Chowringhee Road, Kolkata, Calcutta, West Bengal' | 'India'
    'Marguerite Atelier SARL' | '3 Boulevard Lelasseur, Nantes, Pays de la Loire' | 'France'

## TEST source2
- rows: 4887273
- columns: ['entity_id', 'business_name', 'business_address', 'country']
- empty `business_name`: 0 (0.00%)
- empty `business_address`: 129408 (2.65%)
- empty `country`: 0 (0.00%)
- country value counts:
    'India': 2312565
    'US': 1871330
    'France': 703378
- business_name with non-ASCII chars (possible transliteration): 928158 (18.99%)
- most common last tokens in business_name (legal suffix candidates):
    'limited': 469731
    'ltd': 345704
    'llc': 228438
    'लिमिटेड': 217424
    'inc': 183015
    'private': 120792
    'sarl': 107104
    'center': 98890
    'corp': 89572
    'co': 87794
    'sas': 75400
    'services': 75021
    'partners': 69342
    'group': 69223
    'llp': 60116
    'holdings': 58923
    'लि': 40478
    'corporation': 37776
    'లిమిటెడ్': 37649
    'pvt': 37305
- exact duplicate (non-empty) business_name rows: 576232
- addresses with landmark references (near/opposite/behind/...): 226639 (4.64%)
- addresses with a 5-6 digit number (possible ZIP/PIN): 247928 (5.07%)
- addresses with non-ASCII chars: 720665 (14.75%)
- sample rows (name | address | country):
    'OUTSHlNE  FLAVOUR PRIVATE LIMITED' | 'পশ্চিমবঙ্গ, 40/, WOMESH CHANDRA BANERJEE STREET, KOLKATA' | 'India'
    'SILVA, OUBRE LOVEJOY SERVICES' | 'GENESEE STREET, CAYUAG, NY' | 'US'
    'Holcombe, Smith  and Sylvia Jpmorgan PLLC' | 'BOSTON, 465 8ND STREET, MA' | 'US'
    'Avyakta Solution Limited' | 'H.NO ##6 , 1ST FLOOR, ANSUL PLAZA MARKET SHALIMAR BAGH, DELHI, दिल्ली' | 'India'
    'odinternational.com' | 'SAMVED SANKUL APARTMENT, NAGPUR, Maharashtra' | 'India'

## TEST source3
- rows: 5082316
- columns: ['entity_id', 'business_name', 'business_address', 'country']
- empty `business_name`: 0 (0.00%)
- empty `business_address`: 136098 (2.68%)
- empty `country`: 0 (0.00%)
- country value counts:
    'India': 2405000
    'US': 1945701
    'France': 731615
- business_name with non-ASCII chars (possible transliteration): 737515 (14.51%)
- most common last tokens in business_name (legal suffix candidates):
    'limited': 590653
    'ltd': 370893
    'llc': 245722
    'inc': 190305
    'private': 126844
    'लिमिटेड': 121891
    'center': 119919
    'sarl': 111009
    'services': 89614
    'co': 87200
    'corp': 86766
    'sas': 78051
    'partners': 77530
    'llp': 70811
    'group': 70281
    'holdings': 58347
    'service': 39733
    'pvt': 37761
    'corporation': 34914
    'eurl': 33134
- exact duplicate (non-empty) business_name rows: 560387
- addresses with landmark references (near/opposite/behind/...): 177284 (3.49%)
- addresses with a 5-6 digit number (possible ZIP/PIN): 256051 (5.04%)
- addresses with non-ASCII chars: 729222 (14.35%)
- sample rows (name | address | country):
    'White Trading LLP' | 'Door No ##97 Lakshmi Vilasam, Pathanamthitta, കേരളം' | 'India'
    'Hot Exim Industries Private Limited' | 'A/36, Birla Colony Phulwari Sarif, Patna, BR' | 'India'
    'சில்வர் டெக்னாலஜீஸ் புரொவிஷன் பிரைவேட் லிமிடெட்' | 'No 252 - 1, Punjai Puliampatti, Erode, TN' | 'India'
    '2359madisonavenue.Com' | '01160 Kirkland Avenue, Nashville, Tennessee' | 'US'
    'ওয়ান সফটওয়্যার প্রাইভেট লিমিটেড' | '256/7/A/1 Lokepur (Main Road), Bankura, পশ্চিমবঙ্গ' | 'India'