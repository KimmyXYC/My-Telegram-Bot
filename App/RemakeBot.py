import numpy as np
import random


async def remake(bot, message, rd_data, rd_weights):
    country_choice = np.random.choice(rd_data, p=np.array(rd_weights) / sum(rd_weights))
    sex_choice = random.choice(["男孩子", "女孩子", "MtF", "FtM", "MtC", "萝莉", "正太", "武装直升机", "沃尔玛购物袋",
                                "星巴克", "太监", "无性别", "扶她", "死胎"])
    await bot.reply_to(message, f"转生成功！您现在是 {country_choice} 的 {sex_choice} 了。")
    return country_choice, sex_choice
