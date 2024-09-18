import pygame
import random
import time
import os

# 初始化 Pygame
pygame.init()

# 定义常量
WIDTH, HEIGHT = 700, 850  # 窗口尺寸
ROWS, COLS = 7, 7  # 游戏区域的行数和列数
TILE_SIZE = WIDTH // COLS  # 根据列数计算图块大小
FPS = 30
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BG_COLOR = (245, 222, 179)  # 背景色：小麦色
SLOT_BG_COLOR = (210, 180, 140)  # 槽区背景色：巧克力色
SLOT_BORDER_COLOR = (139, 69, 19)  # 槽区边框颜色：褐色

# 获取当前文件所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 创建窗口
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("星穹铁道，启动！")

# 定义资源路径
image_path = os.path.join(BASE_DIR, "images")
font_path = os.path.join(BASE_DIR, "fonts", "方正大雅宋简体.TTF")  # 请确保字体文件存在于指定路径
music_path = os.path.join(BASE_DIR, "music")

# 加载图案图片 (0.png 到 4.png)
patterns = []
for i in range(5):
    image_file = os.path.join(image_path, f"{i}.png")
    try:
        image = pygame.image.load(image_file)
        image = pygame.transform.scale(image, (TILE_SIZE, TILE_SIZE))
        patterns.append(image)
    except pygame.error as e:
        print(f"无法加载图片 {image_file}: {e}")
        pygame.quit()
        quit()

# 加载支持中文的字体
try:
    font = pygame.font.Font(font_path, 36)  # 设置字体大小为36
except FileNotFoundError:
    print(f"无法找到字体文件：{font_path}")
    pygame.quit()
    quit()

# 加载广告图片
ad_image_path = os.path.join(image_path, "ad.png")
try:
    ad_image = pygame.image.load(ad_image_path)
    ad_image = pygame.transform.scale(ad_image, (WIDTH, HEIGHT))
except pygame.error as e:
    print(f"无法加载广告图片 {ad_image_path}: {e}")
    pygame.quit()
    quit()


# 加载背景图片
def load_image(path, width=WIDTH, height=HEIGHT):
    try:
        image = pygame.image.load(path)
        image = pygame.transform.scale(image, (width, height))
        return image
    except pygame.error as e:
        print(f"无法加载图片 {path}: {e}")
        pygame.quit()
        quit()


game_bg_image = load_image(os.path.join(image_path, "game_bg.png"))
revive_bg_image = load_image(os.path.join(image_path, "revive_bg.png"))
ad_bg_image = load_image(os.path.join(image_path, "ad_bg.png"))
game_win_bg_image = load_image(os.path.join(image_path, "game_win_bg.png"))
game_lose_bg_image = load_image(os.path.join(image_path, "game_lose_bg.png"))

# 初始化混音器
pygame.mixer.init()

# 加载背景音乐和音效
bg_music_path = os.path.join(music_path, "HOYO-MiX - A Dramatic Irony.mp3")
match_sound_path = os.path.join(music_path, "ui.mp3")
victory_sound_path = os.path.join(music_path, "张杰 _ HOYO-MiX - 不眠之夜.mp3")
defeat_sound_path = os.path.join(music_path, "out.mp3")

try:
    pygame.mixer.music.load(bg_music_path)
except pygame.error as e:
    print(f"无法加载背景音乐 {bg_music_path}: {e}")
    pygame.quit()
    quit()

try:
    match_sound = pygame.mixer.Sound(match_sound_path)
except pygame.error as e:
    print(f"无法加载音效 {match_sound_path}: {e}")
    pygame.quit()
    quit()

try:
    victory_sound = pygame.mixer.Sound(victory_sound_path)
except pygame.error as e:
    print(f"无法加载胜利音效 {victory_sound_path}: {e}")
    pygame.quit()
    quit()

try:
    defeat_sound = pygame.mixer.Sound(defeat_sound_path)
except pygame.error as e:
    print(f"无法加载失败音效 {defeat_sound_path}: {e}")
    pygame.quit()
    quit()

# 播放背景音乐
pygame.mixer.music.play(-1)  # -1 表示循环播放

# 定义槽，最多容纳7个图案
slot = []
SLOT_CAPACITY = 7
SLOT_X = (WIDTH - SLOT_CAPACITY * TILE_SIZE) // 2
SLOT_Y = HEIGHT - TILE_SIZE - 20  # 槽区位置调整到最底部

# 定义游戏板尺寸
LAYERS = 3  # 层数，可以根据需要调整

# 定义复活次数
revive_used = False


# 生成游戏板，三维列表表示层、行、列
# 生成游戏板，三维列表表示层、行、列
def generate_boards():
    total_tiles = LAYERS * ROWS * COLS  # 根据选择的层数生成游戏板
    tile_pool = []

    # 创建所有图案的数量，确保可以被3整除
    num_tiles = ((total_tiles + 2) // 3) * 3  # 调整为大于等于 total_tiles 的最小3的倍数
    for i in range(num_tiles // 3):
        tile = patterns[i % len(patterns)]
        tile_pool.extend([tile, tile, tile])  # 每种图案出现三次

    random.shuffle(tile_pool)

    boards = [[[None for _ in range(COLS)] for _ in range(ROWS)] for _ in range(LAYERS)]

    # 将图案随机放置在游戏板上
    for layer in range(LAYERS):
        for row in range(ROWS):
            for col in range(COLS):
                if tile_pool:
                    boards[layer][row][col] = tile_pool.pop()
                else:
                    boards[layer][row][col] = None
    return boards

# 读取排行榜数据，区分难度
def read_scores(difficulty):
    try:
        # 根据难度读取不同的排行榜文件
        filename = f"scores_{difficulty}.txt"
        with open(filename, "r") as file:
            scores = [int(line.strip()) for line in file.readlines()]
    except FileNotFoundError:
        scores = []  # 如果文件不存在，返回一个空列表
    return scores

# 保存排行榜数据，区分难度
def save_scores(scores, difficulty):
    # 根据难度保存到不同的排行榜文件
    filename = f"scores_{difficulty}.txt"
    with open(filename, "w") as file:
        for score in scores:
            file.write(f"{score}\n")




# 绘制游戏板
def draw_board(boards):
    for layer in range(LAYERS):
        for row in range(ROWS):
            for col in range(COLS):
                tile = boards[layer][row][col]
                if tile:
                    x = col * TILE_SIZE
                    y = row * TILE_SIZE
                    # 为了体现层次感，可以根据 layer 调整 x 和 y
                    offset = (LAYERS - layer - 1) * 5  # 每层偏移，制造3D效果
                    screen.blit(tile, (x + offset, y + offset))


# 绘制槽
def draw_slot():
    # 绘制槽背景
    pygame.draw.rect(screen, SLOT_BG_COLOR,
                     (SLOT_X - 5, SLOT_Y - 5, SLOT_CAPACITY * TILE_SIZE + 10, TILE_SIZE + 10))
    # 绘制槽边框
    pygame.draw.rect(screen, SLOT_BORDER_COLOR,
                     (SLOT_X - 5, SLOT_Y - 5, SLOT_CAPACITY * TILE_SIZE + 10, TILE_SIZE + 10), 2)

    # 绘制槽中的图案
    for i, tile in enumerate(slot):
        x = SLOT_X + i * TILE_SIZE
        y = SLOT_Y
        screen.blit(tile, (x, y))


# 处理点击事件
def handle_click(x, y, boards):
    tile_info = get_tile_at_pos(x, y, boards)
    if tile_info:
        layer, row, col = tile_info
        tile = boards[layer][row][col]
        if tile and not is_tile_covered(layer, row, col, boards):
            # 将图案添加到槽中
            slot.append(tile)
            # 从游戏板中移除
            boards[layer][row][col] = None
            # 检查槽中是否有三个相同的图案
            check_slot()
            return True
    return False


# 获取点击的图案位置
def get_tile_at_pos(x, y, boards):
    for layer in reversed(range(LAYERS)):  # 从上到下检查
        for row in range(ROWS):
            for col in range(COLS):
                tile = boards[layer][row][col]
                if tile:
                    tile_x = col * TILE_SIZE + (LAYERS - layer - 1) * 5
                    tile_y = row * TILE_SIZE + (LAYERS - layer - 1) * 5
                    rect = pygame.Rect(tile_x, tile_y, TILE_SIZE, TILE_SIZE)
                    if rect.collidepoint(x, y):
                        return layer, row, col
    return None


# 检查图案是否被遮挡
def is_tile_covered(layer, row, col, boards):
    # 只检查上层同一位置的图案
    if layer + 1 >= LAYERS:
        return False
    upper_layer = layer + 1
    upper_tile = boards[upper_layer][row][col]
    if upper_tile:
        upper_tile_center = (
            col * TILE_SIZE + (LAYERS - upper_layer - 1) * 5 + TILE_SIZE // 2,
            row * TILE_SIZE + (LAYERS - upper_layer - 1) * 5 + TILE_SIZE // 2
        )
        current_tile_center = (
            col * TILE_SIZE + (LAYERS - layer - 1) * 5 + TILE_SIZE // 2,
            row * TILE_SIZE + (LAYERS - layer - 1) * 5 + TILE_SIZE // 2
        )
        if abs(upper_tile_center[0] - current_tile_center[0]) < TILE_SIZE // 2 and \
                abs(upper_tile_center[1] - current_tile_center[1]) < TILE_SIZE // 2:
            return True
    return False


# 检查槽中的图案，是否可以消除
def check_slot():
    global slot
    counts = {}
    # 统计槽中每种图案的数量
    for tile in slot:
        key = patterns.index(tile)  # 使用图案在 patterns 中的索引作为唯一标识
        counts[key] = counts.get(key, 0) + 1
    # 找到数量达到3的图案，进行消除
    to_remove_keys = [key for key, count in counts.items() if count >= 3]
    if to_remove_keys:
        match_sound.play()  # 播放消除音效
    # 从槽中移除消除的图案
    for key in to_remove_keys:
        remove_count = 0
        new_slot = []
        for tile in slot:
            if patterns.index(tile) == key and remove_count < 3:
                remove_count += 1
            else:
                new_slot.append(tile)
        slot = new_slot


# 检查游戏是否结束
# 检查游戏是否结束
def check_game_over(boards, score, difficulty):
    # 检查是否胜利
    if all(tile is None for layer in boards for row in layer for tile in row):
        draw_game_over("你赢了！", score, difficulty)  # 传递当前分数和难度
        return True
    # 检查是否失败
    if len(slot) > SLOT_CAPACITY:
        # 检查是否可以复活
        if not revive():
            draw_game_over("游戏失败！", score, difficulty)  # 传递当前分数和难度
            return True
        else:
            return False
    return False




# 显示排行榜
def draw_scoreboard(scores):
    title_font = pygame.font.Font(font_path, 36)
    title_text = title_font.render("排行榜", True, WHITE)
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 2 + 100))

    score_font = pygame.font.Font(font_path, 30)
    for i, score in enumerate(scores[:3]):  # 只显示前3个分数
        score_text = score_font.render(f"{i + 1}. {score}", True, WHITE)
        screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2 + 150 + i * 40))


# 复活功能
def revive():
    global revive_used, slot
    if not revive_used:
        revive_used = True
        # 显示复活界面
        return show_revive_screen()
    else:
        return False


def show_revive_screen():
    waiting = True
    choice_made = False
    choice = False

    def set_choice(value):
        nonlocal choice_made, choice
        choice_made = True
        choice = value

    while waiting:
        # 显示复活界面的背景图片
        screen.blit(revive_bg_image, (0, 0))

        title_font = pygame.font.Font(font_path, 50)
        text = title_font.render("观看3s广告复活", True, WHITE)
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 3))

        # 绘制按钮
        draw_button("观看广告", WIDTH // 2 - 100, HEIGHT // 2, 200, 50,
                    (200, 200, 200), (150, 150, 150), lambda: set_choice(True))
        draw_button("放弃", WIDTH // 2 - 100, HEIGHT // 2 + 100, 200, 50,
                    (200, 200, 200), (150, 150, 150), lambda: set_choice(False))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        if choice_made:
            if choice:
                # 显示广告图片，等待3秒
                show_ad()
                return True
            else:
                return False


def show_ad():
    start_time = time.time()
    ad_duration = 3  # 广告时长 3 秒
    skip_allowed = False  # 是否允许跳过广告

    while True:
        elapsed_time = time.time() - start_time
        screen.blit(ad_bg_image, (0, 0))
        screen.blit(ad_image, (0, 0))

        # 显示倒计时
        remaining_time = max(0, int(ad_duration - elapsed_time))
        countdown_text = font.render(f"广告剩余 {remaining_time} 秒", True, WHITE)
        screen.blit(countdown_text, (WIDTH // 2 - countdown_text.get_width() // 2, HEIGHT - 100))

        # 如果允许跳过，显示跳过按钮
        if skip_allowed or elapsed_time >= ad_duration:
            draw_button("关闭广告", WIDTH - 150, 20, 120, 40,
                        (200, 0, 0), (255, 0, 0), lambda: return_from_ad())

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            elif (event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.KEYDOWN) and (
                    skip_allowed or elapsed_time >= ad_duration):
                return

        # 广告播放完毕，允许跳过
        if elapsed_time >= ad_duration:
            skip_allowed = True

        pygame.time.Clock().tick(FPS)


def return_from_ad():
    # 返回游戏
    pass  # 这里只是占位，函数体为空


# 游戏结束界面

def draw_game_over(message, score, difficulty):
    global running
    # 停止背景音乐
    pygame.mixer.music.stop()

    # 读取排行榜
    scores = read_scores(difficulty)

    # 添加当前分数并排序，保留前 5 名
    scores.append(score)
    scores = sorted(scores, reverse=True)[:5]  # 只保留最高的5个分数

    # 保存更新后的排行榜
    save_scores(scores, difficulty)

    # 根据游戏结果选择背景图片并播放对应的音效
    if message == "你赢了！":
        victory_sound.play()
        screen.blit(game_win_bg_image, (0, 0))
    else:
        defeat_sound.play()
        screen.blit(game_lose_bg_image, (0, 0))

    large_font = pygame.font.Font(font_path, 60)  # 使用更大的字体
    text_color = WHITE  # 根据背景图片调整文字颜色
    text = large_font.render(message, True, text_color)
    screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 30))

    # 显示当前分数和排行榜
    draw_scoreboard(scores)

    # 倒计时逻辑
    countdown_time = 3  # 倒计时 3 秒
    font = pygame.font.Font(font_path, 30)  # 设置倒计时字体
    start_ticks = pygame.time.get_ticks()  # 获取倒计时开始时间

    # 循环更新倒计时
    while countdown_time > 0:
        screen.fill(BLACK)

        # 根据游戏结果重新绘制背景和结束文字
        if message == "你赢了！":
            screen.blit(game_win_bg_image, (0, 0))
        else:
            screen.blit(game_lose_bg_image, (0, 0))
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2 - 30))
        draw_scoreboard(scores)

        # 计算剩余时间
        seconds_passed = (pygame.time.get_ticks() - start_ticks) // 1000
        countdown_time = 7 - seconds_passed  # 3秒倒计时

        # 显示倒计时
        countdown_text = font.render(f"返回主菜单 {countdown_time} 秒", True, WHITE)
        screen.blit(countdown_text, (WIDTH // 2 - countdown_text.get_width() // 2, HEIGHT // 2 + 50))

        pygame.display.update()

        # 等待一帧
        pygame.time.Clock().tick(30)

    # 重新播放背景音乐
    pygame.mixer.music.play(-1)

    # 返回主菜单
    return_to_menu()


# 返回主菜单
def return_to_menu():
    # 清除当前游戏状态
    global slot, revive_used
    slot = []
    revive_used = False
    # 调用主菜单
    main_menu()


# 绘制顶部信息（例如标题）
def draw_top_info():
    pass  # 当前未显示任何信息，可以在此添加得分等

# 主函数
def start_game(layers, difficulty):
    global slot, revive_used, LAYERS
    LAYERS = layers
    slot = []
    revive_used = False
    boards = generate_boards()
    game_over = False
    score = 0  # 初始化得分
    timer = 60  # 定义倒计时
    start_ticks = pygame.time.get_ticks()  # 获取游戏开始的时间

    while not game_over:
        screen.fill(BG_COLOR)

        # 计算剩余时间
        seconds = timer - (pygame.time.get_ticks() - start_ticks) // 1000
        if seconds <= 0:
            draw_game_over("时间到了！", score, difficulty)
            game_over = True

        draw_board(boards)
        draw_slot()
        draw_timer(seconds)

        pygame.display.update()
        pygame.time.Clock().tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if handle_click(x, y, boards):
                    score += 10  # 每次消除得 10 分
                    if check_game_over(boards, score, difficulty):  # 传递 difficulty 参数
                        game_over = True






# 绘制倒计时
def draw_timer(seconds):
    timer_font = pygame.font.Font(font_path, 36)
    timer_text = timer_font.render(f"时间: {seconds}", True, BLACK)
    screen.blit(timer_text, (WIDTH - 200, 0))  # 显示在右上角


# 主菜单
def main_menu():
    menu = True
    while menu:
        screen.blit(game_bg_image, (0, 0))

        title_font = pygame.font.Font(font_path, 60)
        text = title_font.render("  星穹铁道，启动！", True, WHITE)
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 4))

        # 绘制难度选择按钮
        draw_button("简单", WIDTH // 2 - 100, HEIGHT // 2 - 80, 200, 50,
                    (200, 200, 200), (150, 150, 150), lambda: start_game(2, "easy"))
        draw_button("困难", WIDTH // 2 - 100, HEIGHT // 2, 200, 50,
                    (200, 200, 200), (150, 150, 150), lambda: start_game(3, "hard"))
        draw_button("地狱", WIDTH // 2 - 100, HEIGHT // 2 + 80, 200, 50,
                    (200, 200, 200), (150, 150, 150), lambda: start_game(4, "hell"))
        draw_button("炼狱", WIDTH // 2 - 100, HEIGHT // 2 + 160, 200, 50,
                    (200, 200, 200), (150, 150, 150), lambda: start_game(5, "purgatory"))
        draw_button("退出", WIDTH // 2 - 100, HEIGHT // 2 + 240, 200, 50,
                    (200, 200, 200), (150, 150, 150), quit_game)

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()



def draw_button(text, x, y, w, h, inactive_color, active_color, action=None):
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()

    if x + w > mouse[0] > x and y + h > mouse[1] > y:
        pygame.draw.rect(screen, active_color, (x, y, w, h))
        if click[0] == 1 and action is not None:
            pygame.time.wait(200)  # 防止过快点击
            action()
    else:
        pygame.draw.rect(screen, inactive_color, (x, y, w, h))

    text_surface = font.render(text, True, WHITE)
    screen.blit(
        text_surface,
        (x + (w - text_surface.get_width()) // 2, y + (h - text_surface.get_height()) // 2),
    )




# 退出游戏函数
def quit_game():
    pygame.quit()
    quit()


# 启动主菜单
main_menu()

pygame.quit()
