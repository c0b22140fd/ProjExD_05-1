import math
import random
import sys
import time
import pygame

import pygame as pg
from pygame.locals import *


WIDTH = 1600  # ゲームウィンドウの幅
HEIGHT = 900  # ゲームウィンドウの高さ


def check_bound(obj: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内か画面外かを判定し，真理値タプルを返す
    引数 obj：オブジェクト（爆弾，こうかとん，ビーム）SurfaceのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj.left < 0 or WIDTH < obj.right:  # 横方向のはみ出し判定
        yoko = False
    if obj.top < 0 or HEIGHT < obj.bottom:  # 縦方向のはみ出し判定
        tate = False
    return yoko, tate


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す
    引数1 org：爆弾SurfaceのRect
    引数2 dst：こうかとんSurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm


class Bird(pg.sprite.Sprite):
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }

    def __init__(self, num: int, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 xy：こうかとん画像の位置座標タプル
        """
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"ex05/fig/{num}.png"), 0, 2.0)
        img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん
        self.imgs = {
            (+1, 0): img,  # 右
            (+1, -1): pg.transform.rotozoom(img, 45, 1.0),  # 右上
            (0, -1): pg.transform.rotozoom(img, 90, 1.0),  # 上
            (-1, -1): pg.transform.rotozoom(img0, -45, 1.0),  # 左上
            (-1, 0): img0,  # 左
            (-1, +1): pg.transform.rotozoom(img0, 45, 1.0),  # 左下
            (0, +1): pg.transform.rotozoom(img, -90, 1.0),  # 下
            (+1, +1): pg.transform.rotozoom(img, -45, 1.0),  # 右下
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10
        self.state = "normal"

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"ex05/fig/{num}.png"), 0, 2.0)
        screen.blit(self.image, self.rect)

    def change_state(self, state: str, hyper_life: int):
        self.state = state
        self.hyper_life = hyper_life

        

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                self.rect.move_ip(+self.speed*mv[0], +self.speed*mv[1])
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        if check_bound(self.rect) != (True, True):
            for k, mv in __class__.delta.items():
                if key_lst[k]:
                    self.rect.move_ip(-self.speed*mv[0], -self.speed*mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.image = self.imgs[self.dire]

        if self.state == "hyper":
            self.image = pg.transform.laplacian(self.image)
            self.hyper_life -= 1
            if self.hyper_life < 0:
                self.change_state("normal",-1)
        screen.blit(self.image, self.rect)

    def get_direction(self) -> tuple[int, int]:
        return self.dire
    

    

class Bomb(pg.sprite.Sprite):
    """
    爆弾に関するクラス
    """
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

    def __init__(self, emy: "Enemy", bird: Bird):
        """
        爆弾円Surfaceを生成する
        引数1 emy：爆弾を投下する敵機
        引数2 bird：攻撃対象のこうかとん
        """
        super().__init__()
        rad = random.randint(10, 50)  # 爆弾円の半径：10以上50以下の乱数
        color = random.choice(__class__.colors)  # 爆弾円の色：クラス変数からランダム選択
        self.image = pg.Surface((2*rad, 2*rad))
        pg.draw.circle(self.image, color, (rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        # 爆弾を投下するemyから見た攻撃対象のbirdの方向を計算
        self.vx, self.vy = calc_orientation(emy.rect, bird.rect)  
        self.rect.centerx = emy.rect.centerx
        self.rect.centery = emy.rect.centery+emy.rect.height/2
        self.speed = 6
        self.cnt = 0

    def update(self):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(+self.speed*self.vx, +self.speed*self.vy)
        if self.cnt == 3:  # 爆弾が壁に3回当たったら
            self.kill()  # 爆弾を削除
        if check_bound(self.rect) == (False, True):  # 左右の壁に当たったとき
            self.vx = -self.vx  # 移動方向を反転する
            self.cnt += 1
        elif check_bound(self.rect) == (True,False):  # 上下の壁に当たったとき
            self.vy = -self.vy  # 方向を反転
            self.cnt += 1



class Beam(pg.sprite.Sprite):
    """
    ビームに関するクラス
    """
    def __init__(self, bird: Bird, spin=0):   #spinの初期値は０
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん
        """
        super().__init__()
        self.vx, self.vy = bird.get_direction()
        angle = math.degrees(math.atan2(-self.vy, self.vx))
        angle += spin #angleにspinを加える
        self.image = pg.transform.rotozoom(pg.image.load(f"ex05/fig/beam.png"), angle, 2.0)
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery+bird.rect.height*self.vy
        self.rect.centerx = bird.rect.centerx+bird.rect.width*self.vx
        self.speed = 10

    def update(self):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(+self.speed*self.vx, +self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()

class Hp: #HPバー
    def __init__(self, x, y, width, max):

        self.x = x
        self.y = y
        self.width = width
        self.max = max # 最大HP
        self.hp = max # HP
        self.mark = int((self.width - 4) / self.max) # HPバーの1目盛り

        self.font = pg.font.SysFont(None, 28)
        self.label = self.font.render("HP", True, (255, 255, 255))
        self.frame = Rect(self.x + 2 + self.label.get_width(), self.y, self.width, self.label.get_height())
        self.bar = Rect(self.x + 4 + self.label.get_width(), self.y + 2, self.width - 4, self.label.get_height() - 4)
        self.value = Rect(self.x + 4 + self.label.get_width(), self.y + 2, self.width - 4, self.label.get_height() - 4)

        self.effect_bar = Rect(self.x + 4 + self.label.get_width(), self.y + 2, self.width - 4, self.label.get_height() - 4)
        self.effect_color = (0, 255, 255)
    
    def update(self):
        if self.hp >= self.max:
            self.hp = self.max
            
        if self.effect_bar.width > self.mark * self.hp:
            self.value.width = self.mark * self.hp
            
        elif self.value.width < self.mark * self.hp:
            self.effect_bar.width = self.mark * self.hp

        # effect_barの色を変える
        if self.effect_bar.width <= self.bar.width / 6:
            self.effect_color = (0, 255, 0)
        elif self.effect_bar.width <= self.bar.width / 2:
            self.effect_color = (0, 255, 0)
        else:
            self.effect_color = (255, 0, 0)

    def draw(self, screen):
        pg.draw.rect(screen, (255, 255, 255), self.frame)
        pg.draw.rect(screen, (0, 0, 0), self.bar)
        pg.draw.rect(screen, self.effect_color, self.effect_bar)
        pg.draw.rect(screen, (0, 255, 0), self.value)
        screen.blit(self.label, (self.x, self.y))


class NeoBeam: #追加機能４弾幕
    def __init__(self, bird:Bird, num:int):
        self.bird = bird
        self.num = num

    def gen_beams(self): #こうかとんに対し-50°~50°の範囲にbeamを発生させる
        beam_ls = []
        for spin in range(-50, 51, 25):
            beam = Beam(self.bird, spin)
            beam_ls.append(beam)
        return beam_ls

class Explosion(pg.sprite.Sprite):
    """
    爆発に関するクラス
    """
    def __init__(self, obj: "Bomb|Enemy", life: int):
        """
        爆弾が爆発するエフェクトを生成する
        引数1 obj：爆発するBombまたは敵機インスタンス
        引数2 life：爆発時間
        """
        super().__init__()
        img = pg.image.load("ex05/fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life

    def update(self):
        """
        爆発時間を1減算した爆発経過時間_lifeに応じて爆発画像を切り替えることで
        爆発エフェクトを表現する
        """
        self.life -= 1
        self.image = self.imgs[self.life//10%2]
        if self.life < 0:
            self.kill()


class Shield(pg.sprite.Sprite):
    def __init__(self,bird: Bird,life : int):
         super().__init__()
         self.image = pg.Surface((20,bird.rect.height*2))
         pg.draw.rect(self.image,(0,0,0),pg.Rect(0,0, 20, bird.rect.height*2))
         self.rect = self.image.get_rect()
         self.rect.centerx = bird.rect.centerx+50
         self.rect.centery = bird.rect.centery
         self.life = life
         
    def update(self):
        self.life -= 1
        if self.life < 0:
            self.kill() #Shiledsグループからの削除


class Enemy(pg.sprite.Sprite):
    """
    敵機に関するクラス
    """
    imgs = [pg.image.load(f"ex05/fig/alien{i}.png") for i in range(1, 4)]
    
    def __init__(self):
        super().__init__()
        self.image = random.choice(__class__.imgs)
        self.rect = self.image.get_rect()
        self.rect.center = random.randint(0, WIDTH), 0
        self.vy = +6
        self.bound = random.randint(50, HEIGHT/2)  # 停止位置
        self.state = "down"  # 降下状態or停止状態
        self.interval = random.randint(50, 300)  # 爆弾投下インターバル

    def update(self):
        """
        敵機を速度ベクトルself.vyに基づき移動（降下）させる
        ランダムに決めた停止位置_boundまで降下したら，_stateを停止状態に変更する
        引数 screen：画面Surface
        """
        if self.rect.centery > self.bound:
            self.vy = 0
            self.state = "stop"
        self.rect.centery += self.vy


class Score:
    """
    打ち落とした爆弾，敵機の数をスコアとして表示するクラス
    爆弾：1点
    敵機：10点
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.score = 0
        self.image = self.font.render(f"Score: {self.score}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

    def score_up(self, add):
        self.score += add

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.score}", 0, self.color)
        screen.blit(self.image, self.rect)
class Reload:
    """
    時間を計測するして、表示するクラス
    """
    def __init__(self, start,fr):
        """
        start = 初期値
        fr = フレームレート
        """
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.start = start//fr
        self.image = self.font.render(f"Reloadtime: {self.start}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 125, HEIGHT-25 

    def time_up(self, add):
        self.start += add

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Reloadtime: {self.start}", 0, self.color)
        screen.blit(self.image, self.rect)

class Finish:
    """
    プログラムを終わらせるためのボタン表示
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.image = self.font.render(f"Finish = Enter", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 1430, HEIGHT-50

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Finish = Enter", 0, self.color)
        screen.blit(self.image, self.rect)

class Continue:
    """
    プログラムを続けるためのボタン表示
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.image = self.font.render(f"Continue = Space", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 1410, HEIGHT-80

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Continue = Space", 0, self.color)
        screen.blit(self.image, self.rect)

class Gravity(pg.sprite.Sprite):
    """
    重力球の追加
    """
    def __init__(self, bird, size, life):
        super().__init__()
        #self.rad =  size # ジュウリョクダマの半径：size
        color = (1, 1, 1)  # 重力タマの色：黒
        self.image = pg.Surface((2*size, 2*size))
        pg.draw.circle(self.image, color, (size, size), size)
        self.image.set_colorkey((0, 0, 0))
        self.image.set_alpha(200)
        self.rect = self.image.get_rect()
        self.rect.centerx = bird.rect.centerx
        self.rect.centery = bird.rect.centery
        self.life = life
        #self.speed = bird.speed
    def update(self, ):#key_lst)これを追加すれば、球がついてくる機能を有効化できる。:
        """
        以下は球がついてくるようになる追加機能である。
        sum_mv = [0, 0]
        for k, mv in Bird.delta.items():
            if key_lst[k]:
                self.rect.move_ip(+self.speed*mv[0], +self.speed*mv[1])
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        if check_bound(self.rect) != (True, True):
            for k, mv in Bird.delta.items():
                if key_lst[k]:
                    self.rect.move_ip(-self.speed*mv[0], -self.speed*mv[1])
        """
        self.life -= 1
        if self.life < 0:
            self.kill()

class fire(pg.sprite.Sprite): 
    "焼野原の追加"
    def __init__(self,bird: Bird,life : int):
         super().__init__()
         self.image = pg.Surface((6800,900))
         color = (245,120,0)
         pg.draw.rect(self.image,color,pg.Rect(0,0, 6800,900))
         self.image.set_alpha(200)
         self.rect = self.image.get_rect()
         self.rect.centerx = 0
         self.rect.centery = 900
         self.life = life
    """
    def update(self):
        self.life -= 1
        if self.life < 0:
            self.kill() #fireグループからの削除
    """

def main():
    pg.display.set_caption("逆襲！エイリアン")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("ex05/fig/pg_bg.jpg")
    clear_img = pg.image.load("ex05/fig/text_gameclear.png")
    score = Score()
    finish = Finish()
    conti =Continue()
    bg_img = pg.image.load("ex05/fig/pg_bg.jpg")
    score = Score()
    font1 = pygame.font.SysFont(None, 50)
    bird = Bird(3, (900, 400))
    hp = Hp(40, 800, 100, 4)
    bombs = pg.sprite.Group()
    beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()
    Shields = pg.sprite.Group()
    i = 0 #クリア後の分岐のための真偽値
    fires = pg.sprite.Group()

    gravity = pg.sprite.Group()
    tmr = 0
    clock = pg.time.Clock()
    re = 0
    count = 0
    re_time = False
    while True:
        key_lst = pg.key.get_pressed()
        shift_pressed = False
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE and (re ==0 or tmr/50>re+5) :#ビームを５回以上だした後に５秒たったら
                beams.add(Beam(bird))
                count += 1#出した数ビームの数
                if count >= 5:#出したビームの数が５いじょうなら
                    re = tmr/50#時間を記録
                    re_time = Reload(re-tmr//50, 50)#Reloadクラスのインスタンス作成
                    count = 0#出したビームの数を０にする
                if pg.key.get_mods() & pg.KMOD_LSHIFT :
                    count += 5#出した数ビームの数
                    if count >= 5:
                        count = 0
                        re = tmr/50
                        re_time = Reload(re-tmr//50, 50)
                    shift_pressed = True
            if event.type == pg.KEYDOWN and event.key == pg.K_CAPSLOCK:
                if score.score >= 10 and len(Shields) == 0:
                    Shields.add(Shield(bird,400))
                    score.score -= 50

            if event.type == pg.KEYDOWN and event.key == pg.K_RSHIFT and score.score >= 100:
                bird.change_state("hyper",500)
                score.score_up(-100)
            if event.type == pg.KEYDOWN and event.key == pg.K_LSHIFT:
                bird.speed = 20
            if event.type == pg.KEYUP and event.key == pg.K_LSHIFT:
                bird.speed = 10
            if event.type == pg.KEYDOWN and event.key == pg.K_TAB and score.score >= 50:
                score.score_up(-50)
                gravity.add(Gravity(bird, 200, 500))

            if event.type == pg.KEYDOWN and event.key == pg.K_RETURN:
                pg.quit()
                sys.exit()
            if i != 0 and event.type == pg.KEYDOWN and event.key == pg.K_SPACE: #クリア後スペースを押すともう一度プレイできる
                main()

            if score.score >= 50 and len(fires) == 0:
                    fires.add(fire(bird,400))

            
        screen.blit(bg_img, [0, 0])

        if tmr%200 == 0:  # 200フレームに1回，敵機を出現させる
            emys.add(Enemy())

        for emy in emys:
            if emy.state == "stop" and tmr%emy.interval == 0:
                # 敵機が停止状態に入ったら，intervalに応じて爆弾投下
                bombs.add(Bomb(emy, bird))

        for emy in pg.sprite.groupcollide(emys, beams, True, True).keys():
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            score.score_up(10)  # 10点アップ
            bird.change_img(6, screen)  # こうかとん喜びエフェクト

        for bomb in pg.sprite.groupcollide(bombs, beams, True, True).keys():
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.score_up(1)  # 1点アップ

        for bomb in pg.sprite.spritecollide(bird, bombs, True):
            if bird.state == "hyper":
                exps.add(Explosion(bomb, 50))  # 爆発エフェクト
                score.score_up(1)  # 1点アップ
            
            else:
                exps.add(Explosion(bomb, 50)) #爆発エフェクト
                hp.hp -= 1 #㏋　ー１
                if hp.hp == 0: #HPがなくなったら
                    bird.change_img(8, screen) # こうかとん悲しみエフェクト
                    score.update(screen)
                    pg.display.update()
                    time.sleep(2)
                    return

        for bomb in pg.sprite.groupcollide(bombs,gravity, True, False).keys():
            exps.add(Explosion(bomb, 50))

        if len(pg.sprite.spritecollide(bird, bombs, True)) != 0:
            exps.add(Explosion(bomb, 50)) #爆発エフェクト
            hp.hp -= 1 #HP -1
            if hp.hp == 0: #HPがなくなったら
                bird.change_img(8, screen) # こうかとん悲しみエフェクト
                score.update(screen)
                pg.display.update()
                time.sleep(2)
                return
        
        if len(pg.sprite.spritecollide(bird, fires, True)) != 0:#こうかとんが火（オレンジの四角）に触れたら負け
            bird.change_img(10, screen) # 焼き鳥の画像
            score.update(screen)
            text1 = font1.render("grilled chicken", True, (255,64,64))
            screen.blit(text1, (500,500))#火にあたって負けた場合のメッセージ
            pg.display.update()
            time.sleep(2)
            return
        
        if len(pg.sprite.spritecollide(bird, emys, True)) != 0: #こうかとんが敵に触れたら負け
            bird.change_img(8, screen) # こうかとん悲しみエフェクト
            score.update(screen)
            pg.display.update()
            time.sleep(2)
            return
        
        for bomb in pg.sprite.groupcollide(bombs, Shields, True, False).keys():
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.score_up(1)

        gravity.update()#key_lst)これを有効化すると、球がついてくる。
        gravity.draw(screen)
        if shift_pressed: #左shiftおされたら
            if pg.key.get_mods() & pg.KMOD_LSHIFT:
                num_beams = 5
                neo_beam = NeoBeam(bird, num_beams)
                beams.add(*neo_beam.gen_beams())

        if score.score >= 300 : #scoreが300点以上になると
            screen.blit(bg_img, [0, 0])
            screen.blit(clear_img, [300, 200]) # ゲームクリア
            i = 1 #クリア後というのを示す
            score.update(screen) #スコア表示
            finish.update(screen) #終わらせるボタンを表示
            conti.update(screen) #続けるボタンを表示
            pg.display.update()
        
        if i == 0: #クリアしていない時に実行するもの
            bird.update(key_lst, screen)
            beams.update()
            beams.draw(screen)
            hp.update()
            hp.draw(screen)
            emys.update()
            emys.draw(screen)
            bombs.update()
            bombs.draw(screen)
            exps.update()
            exps.draw(screen)
            Shields.update() #防御壁の更新
            Shields.draw(screen) #防御壁の描画
            fires.update()#焼野原の更新
            fires.draw(screen) #焼野原の描画
            if re_time:
                if tmr % 50 == 0:
                    re_time.time_up(1)
                if re_time.start <= 5:
                    re_time.update(screen)

            score.update(screen)
            pg.display.update()
            tmr += 1
            clock.tick(50)
        else:
            if event.type == pg.KEYDOWN and event.key == pg.K_RETURN: #エンターキーを押したときにプログラムを終了
                pg.quit()
                sys.exit()

if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
