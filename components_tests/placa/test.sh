array=(5 15 19 21 23 10 12 16 18 22 24 26 32 36 38 40)

gpiofind PIN_5
for i in "${array[@]}"
do 
	echo "PIN $i: "
	gpiofind "PIN_$i"
done
