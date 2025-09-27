Plan how to add support for continuous long chat responses - in which case the bot will split the response in logical points.

This means, the latest new line, that still fits the response length of Discord.

When the response is split, each chunk starting from second will start with "</ continuing>\n" and then continue.

If the answer has 3 backticks for code block and then it gets split, the code will add them in current split chunk, and next response chunk will start with "</ continuing>\n" and then add another 3 backticks before continuing the response.

