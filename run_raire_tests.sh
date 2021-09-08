
for instance in RaireData/Input/*.raire; do
    bn=`basename ${instance}`
    echo "Running test on instance $bn"
    python3.8 test_raire.py ${instance} RaireData/Output/${bn}.out 
done

for instance in RaireData/Input/NSW2015/*.raire; do
    bn=`basename ${instance}`
    echo "Running test on instance $bn"
    python3.8 test_raire.py ${instance} RaireData/Output/NSW2015_Output/${bn}.out 
done
