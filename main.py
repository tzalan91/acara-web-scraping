# This is a sample Python script.

# Press Mayús+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import acara_web_scraper as aws
from flask import Flask
from flask import jsonify
from flask import request
import json

def main():
    # Instance the web scraper
    ws = aws.AcaraWebScraper()
    ws.scrap_brands()

    # Instance the Flask Server
    app = Flask(__name__)

    # Get the brands
    @app.route('/brands', methods=['GET'])
    def get_brands():
        return jsonify(ws.scrap_brands())

    # Get the models
    @app.route('/models', methods=['GET'])
    def get_models():
        brands_to_query = [str(request.args.get('brand'))]
        models = ws.scrap_models(brands_to_query)
        return jsonify(models)

    # Get the prices
    @app.route('/prices', methods=['GET'])
    def get_prices():
        # Brand to query and his models
        brands_to_query = [str(request.args.get('brand'))]
        models = ws.scrap_models(brands_to_query)

        # Filter the model selected
        model = str(request.args.get('model'))
        models = ws.filter_models(model)

        # Get the prices
        l_prices = ws.scrap_price_from_model(models[0])

        return jsonify(l_prices)

    # Starting the app
    app.run(host='localhost', port=5000)

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()