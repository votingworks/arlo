
for instance in RaireData/Input/*.raire; do
    bn=`basename ${instance}`
    echo "Running test on instance $bn"
    python3.8 test_raire.py -i ${instance} -o RaireData/Output/${bn}.out 
done

for instance in RaireData/Input/NSW2015/*.raire; do
    bn=`basename ${instance}`
    echo "Running test on instance $bn"
    python3.8 test_raire.py -i ${instance} -o RaireData/Output/NSW2015_Output/${bn}.out 
done

python3.8 test_raire.py -i RaireData/Input/SpecialCases/SanFran_2007.raire -o RaireData/Output/SpecialCases/SanFran_2007.raire.out -agap 0.00001
