<p align="center">
  <h1 align="center">TXT-LEECH-BOT</h1>
</p>

A Telegram bot that can download videos from text files containing links, with support for DRM protected content.

## Features

- Download videos from text files
- Support for multiple video qualities
- DRM protected content support
- Custom thumbnail support
- Progress tracking
- Batch processing

## Deployment Methods

### Deploy to Heroku
[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/20255-ee-085/TXT-LEECH-BOT)

1. Create a Heroku account (skip if you already have one)
2. Click the Deploy button above
3. Fill in the required environment variables:
   - `API_ID`: Get from my.telegram.org
   - `API_HASH`: Get from my.telegram.org
   - `BOT_TOKEN`: Get from @BotFather
4. Click "Deploy App"
5. Once deployed, ensure the worker dyno is enabled

### Google Colab
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/20255-ee-085/TXT-LEECH-BOT/blob/main/TXT_Leech_Bot.ipynb)

1. Open the Colab notebook using the button above
2. Fill in your credentials in the notebook
3. Run all cells
4. Bot will be active while the Colab notebook is running

### Local Deployment

1. Clone the repository
```bash
git clone https://github.com/20255-ee-085/TXT-LEECH-BOT
cd TXT-LEECH-BOT
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Create .env file with your credentials
```
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
```

4. Run the bot
```bash
python3 main.py
```

## Environment Variables

- `API_ID` - Get from my.telegram.org
- `API_HASH` - Get from my.telegram.org
- `BOT_TOKEN` - Get from @BotFather

## Commands

- `/start` - Check if bot is alive
- `/upload` - Start the download process
- `/stop` - Stop ongoing process

## Credits

- Created by [@JOHN FR34K](https://t.me/JOHN_FR34K)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.