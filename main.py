import importer, sys

def main():
	mode = ''
	if len(sys.argv) >= 2: mode = sys.argv[1].lower()

	print(mode)

	imp = importer.Importer(mode=mode)
	imp.update()
	imp.output()

if __name__ == '__main__':
	main()
