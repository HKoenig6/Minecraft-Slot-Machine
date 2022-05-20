# Minecraft-Slot-Machine
Welcome to the largest personal project of mine to date!
Further information on the machine can be found via:
   -This youtube link https://youtu.be/OxTlvFjo5VA
   -A minecraft book available in the world save

Feel free to contact me at HKoenig4644@gmail.com for any comments,
questions, etc. on the machine; I am more than happy to explain
any components or flaws in further detail.

File Descriptions:
	dataset- contains cropped images of each symbol, organized in folders by spin.
		The first 100 spins contain a CSV file of the correct symbols for each block,
		used in testing label_image's correctness in importdata.py
	original_world- The creative world that I used for building the machine. Drag
		this folder in your minecraft saves to use it
	raw_images- contains the sample of spins that I screenshotted
	wins- contains a set of MySQL SELECT statements to filter each type of payout from
		the dataset
	importdata.py, runanalyses.py- check documents for comments
	isolated_machine.construction- construction file used in Amulet software, a
		minecraft world editor, that can be pasted into any world
	
