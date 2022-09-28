import importer2, sys

def main():
	mode = ''
	if len(sys.argv) >= 2: mode = sys.argv[1].lower()

	print(mode)

	imp = importer2.Importer(refresh=(mode=="refresh"))
	imp.output()

if __name__ == '__main__':
	main()
