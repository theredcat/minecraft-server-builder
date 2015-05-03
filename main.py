import zipfile as zf, sys
from lxml import html
import requests
import re
import shutil
import tempfile

def log(message, level="info"):
	print "[%s] %s" % (level,message)

def zipCopy(fileread, fileput, zipfilePath):
	tempFile = tempfile.NamedTemporaryFile()
	tempFile.write(fileread.read(zipfilePath))
	fileput.write(tempFile.name,zipfilePath)
	tempFile.close()

def chooseVersion(prompt, url, xpath, mapLambda=lambda x: re.sub(r"[\n\r\t ]","",x)):
	page = requests.get(url)
	tree = html.fromstring(page.text)

	versions = []

	for version in map(mapLambda,tree.xpath(xpath)) :
		if version != "":
			versions.append(version)

	for version in versions:
		print ' - %s' % version

	while True:
		version = raw_input(prompt % versions[0]) or versions[0]
		if any(version in s for s in versions):
			return version


# STEP 1 : Get minecraft version list from files.minecraftforge.net and ask user wich version to use

minecraftVersion = chooseVersion(
	'Choose your Minecraft version [%s] : ', 
	'http://files.minecraftforge.net/', 
	'//div[@class="versions-info"]//li//text()'
)

# STEP 2 : Get Forge version list from files.minecraftforge.net and ask user wich version to use

forgeVersion = chooseVersion(
	'Choose your Forge version [%s] : ', 
	'http://files.minecraftforge.net/maven/net/minecraftforge/forge/index_%s.html' % (minecraftVersion), 
	'//table[@id="downloadsTable"]/tr/td[last()]/ul/li[last()]/a[contains(@class,"info-link")]/@href', 
	mapLambda=lambda x: re.sub(r"^.*/forge-([A-Za-z0-9~._-]*)\-universal.jar$", r"\1", x) 
)

# STEP 3 : Download Forge Universal
log("Downloading Forge Universal...")
response = requests.get("http://files.minecraftforge.net/maven/net/minecraftforge/forge/%s/forge-%s-universal.jar" % (forgeVersion,forgeVersion), stream=True)
forge = tempfile.TemporaryFile()
shutil.copyfileobj(response.raw, forge)
log("Unzipping Forge Universal...")
forgeZip = zf.ZipFile(forge,"r")

log("Downloading Minecraft Server...")
# STEP 4 : Download Minecraft server
response = requests.get("https://s3.amazonaws.com/Minecraft.Download/versions/%s/minecraft_server.%s.jar" % (minecraftVersion,minecraftVersion), stream=True, verify=False)
minecraft = "./server-forge-%s.jar" % (forgeVersion)
with open(minecraft, 'wb') as out_file:
	shutil.copyfileobj(response.raw, out_file)
	out_file.seek(0) # %#/!?]_%^# !!!! => https://hg.python.org/cpython/rev/5102336ca343/ https://mail.python.org/pipermail/python-bugs-list/2007-February/037299.html
	log("Unzipping Minecraft Server.")
	minecraftZip = zf.ZipFile(minecraft, "a")
	log("MC List")
	print len(minecraftZip.namelist())
	for f in forgeZip.namelist():
		zipCopy(forgeZip, minecraftZip, f)

	# STEP 5 : Inject forge into Minecraft server
	#z.write(sys.argv[2], sys.argv[3])
	#z.close()
