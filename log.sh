#!/bin/bash

setup_log(){
    echo -e "[$SECTION_1]" > $OUTPUT
    echo -e "\n[$SECTION_2]" >> $OUTPUT
    echo -e "\n[$SECTION_3]" >> $OUTPUT
    echo -e "\n[$SECTION_4]" >> $OUTPUT

    date | section_1 
}

section_1() {
	tee >(xargs -I {} sed -i "/$SECTION_1/a {}" $OUTPUT)
}

section_2() {
	tee >(xargs -I {} sed -i "/$SECTION_3/i {}" $OUTPUT)
}

section_3() {
	tee >(xargs -I {} sed -i "/$SECTION_4/i {}" $OUTPUT)
}

section_4() {
	tee >(xargs -I {} sed -i "/$SECTION_4/a {}" $OUTPUT)
}