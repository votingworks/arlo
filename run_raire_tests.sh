
for instance in RaireData/Input/*.raire; do
    bn=`basename ${instance}`
    python3.8 test_raire.py ${instance} RaireData/Output/${bn}.out 
done
