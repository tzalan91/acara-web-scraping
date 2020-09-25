from urllib.request import urlopen
from bs4 import BeautifulSoup
import time
import copy
from configparser import RawConfigParser

class AcaraWebScraper :
	CONST_CAR_CATEGORIES = ('AUTOS', 'CAMIONES', 'MAQUINARIA AGRÍCOLA')
	CONST_IGN_CATEGORIES = ('AUTOS', 'CAMIONES', 'MAQUINARIA AGRÍCOLA')

	def read_config_file(self, configFile):
		config = RawConfigParser()
		config.read(configFile)

		self.CONST_ACARA_BASE_URL 			= config.get(self.__class__.__name__, 'ACARA_BASE_URL')
		self.CONST_ACARA_CARS_URL 			= config.get(self.__class__.__name__, 'ACARA_CARS_URL')
		self.CONST_ACARA_TABLE_PRICES_ID 	= config.get(self.__class__.__name__, 'ACARA_TABLE_PRICES_ID')
	
	def __init__(self, brands=[], configFile='ConfigFile.properties'):
		self.brands = brands
		self.read_config_file(configFile)

	def html_to_json(self, html_table, indent=None):
		soup = BeautifulSoup(html_table, "html.parser")
		rows = soup.find_all("tr")

		headers = {}
		thead = soup.find("thead")
		if thead:
			thead = thead.find_all("th")
			for i in range(len(thead)):
				headers[i] = thead[i].text.strip().lower()
		data = []
		for row in rows:
			cells = row.find_all("td")
			if thead:
				items = {}
				for index in headers:
					try:
						items[headers[index]] = cells[index].text
					except:
						items[headers[index]] = ''
			else:
				items = []
				for index in cells:
					items.append(index.text.strip())
			data.append(items)

		return data

	def get_brands(self):
		"""
			Return the currently list of brands
		"""
		return self.brands
	
	def get_models(self):
		"""
			Return the currently list of brands
		"""
		return self.models

	def get_prices(self):
		"""
			Return the currently list of prices
		"""
		return self.prices
	
	def set_brands(self, l_brands):
		"""
			Set the list of brands
		"""
		self.brands = copy.copy(l_brands)
	
	def filter_brands(self, pattern):
		"""
			Set the list of brands
		"""
		self.brands = [ b for b in self.brands if pattern in b ]
	
	def filter_models(self, pattern):
		"""
			Set the list of brands
		"""
		#self.models = self.models[self.models['MODEL'].str.contains(pattern, na=False)]
		self.models = [m for m in self.models if pattern in m["MODEL"]]

		return self.models
	
	def scrap_brands(self):
		"""
			Do the scraping and return the list of brands obtained
		"""
		# Get the base list from the CARS URL
		try:
			html = urlopen(self.CONST_ACARA_BASE_URL+self.CONST_ACARA_CARS_URL)
		
			res = BeautifulSoup(html.read(), "html.parser")
			
			# For each brand, get the name and the URL (href)
			d_brands = dict()
			brands = res.findAll("a", {"class": "link-selector"})
			for brand in brands:
				try:
					# Ignoring the car's categories
					if brand.getText().rstrip().lstrip() not in self.CONST_CAR_CATEGORIES:
						d_brands[brand.getText().rstrip().lstrip()] = self.CONST_ACARA_BASE_URL+str(brand.get_attribute_list('href')[0]).replace(' ', '%20')
				except Exception as e2:
					print("[ERROR] - Error scraping brands from ACARA : {"+str(e2)+"}")
					raise

			print("[INFO ] - Number of brands found: {}".format(len(d_brands.keys())))
			self.brands = copy.copy(d_brands)
			del d_brands
			
			return self.brands
	
		except Exception as e:
			print("[ERROR] - Error scraping brands from ACARA : {"+str(e)+"}")
			raise

	def scrap_models_from_brand(self, brand) -> list:
		"""
			Do the scraping for the car's models for just one brand
		"""
		# Sleep time, to prevent to be banned
		time.sleep(1)

		# Get the base list from each URL, replacing blank spaces with '%20'
		url = self.brands[brand]
		try:
			html = urlopen(url)

			# BeautifulSoup to parse the result
			res = BeautifulSoup(html.read(), "html.parser")

			# For each model found, get the name and added it to the general models list
			models = res.findAll("a", {"class": "opt-select"})
			new_models = [{'BRAND':brand, 'MODEL':model.getText().rstrip().lstrip().upper(), 'URL':self.CONST_ACARA_BASE_URL+str(model.get_attribute_list('href')[0])} for model in models if model.getText().rstrip().lstrip().upper() not in self.CONST_IGN_CATEGORIES]

			return new_models

		except Exception as e:
			print("[ERROR] - Error scraping the models from ACARA for brand: {"+str(brand)+"} - Error : {"+str(e)+"}")
			raise
	
	def scrap_models(self, brands_to_query) -> list:
		"""
			Do the scraping for the car's models based on the brands indicated by parameter or the local brands
		"""
		if len(self.brands) == 0:
			return None

		if len(brands_to_query) == 0:
			brands_to_query = self.brands.keys()
            
		# Now, for each brand we will get the models list from each URL
		l_models = []
		for brand in self.brands:
			if brand in brands_to_query:
				new_models = self.scrap_models_from_brand(brand)
				l_models += new_models
				del new_models

		print("[INFO ] - Total number of models found: {}".format(len(l_models)))
		#df_models = pd.DataFrame(l_models)
		self.models = copy.copy(l_models)

		#del df_models
		del l_models

		return self.models


	def scrap_price_from_model(self, model) -> list:
		"""
			Do the scraping for the car's models prices just for one model
		"""
		# Sleep time, to prevent to be banned
		time.sleep(1)

		# Get the base list from each URL, replacing blank spaces with '%20'
		url = model["URL"].replace(' ', '%20').encode('ascii', 'ignore').decode('ascii')
		html = urlopen(url+"&version=todas")

		# BeautifulSoup to parse the result
		res = BeautifulSoup(html.read(), "html.parser")

		# For each model found, get the prices for each year and added it to the main prices list
		prices_table = res.findAll("table", {"id": self.CONST_ACARA_TABLE_PRICES_ID})
		#df_prices_aux = (pd.read_html(str(prices_table[0])))[0]
		df_prices_aux = self.html_to_json(str(prices_table[0]).encode('ascii', 'ignore').decode('ascii'))

		return df_prices_aux


	def scrap_prices(self, models_to_query) -> list:
		"""
			Do the scraping for the car's models prices based on the models indicated by parameter or the local models
		"""
		if len(self.models) == 0:
			return None

		# Now, for each model we will get the prices from each URL
		df_prices = []
		df_not_found = []
		for k in self.models.keys():
			try:
				model = self.models[k]
				df_prices_aux = self.scrap_price_from_model(model)

				# Add the price to the main prices list
				if len(df_prices) == 0:
					df_prices = copy.copy(df_prices_aux)
				else:
					df_prices = (df_prices + copy.copy(df_prices_aux))
					#df_prices = pd.concat([df_prices, copy.copy(df_prices_aux)])

			except Exception as e:
				print("[ERROR] - Error scraping the price's model from ACARA for model: {"+str(model["MODEL"])+"} - Error : {"+str(e)+"}")

		print("[INFO ] - Total number of prices found: {}".format(len(df_prices)))
		#print("[INFO ] - Total number of prices not-found: {}".format(len(df_not_found)))

		self.prices = copy.copy(df_prices)
		self.prices_not_found =  copy.copy(df_not_found)

		del df_prices
		del df_not_found

		return self.prices, self.prices_not_found