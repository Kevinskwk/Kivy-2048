from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.uix.popup import Popup
from kivy.animation import Animation

import numpy as np
import time
import random

import pickle

tile_color_map = {
    0: (0, 0.5, 0, 1),
    2: (0, 1, 0, 1),
    4: (0, 0.8, 0.2, 1),
    8: (0, 0.6, 0.4, 1),
    16: (0, 0.4, 0.6, 1),
    32: (0, 0.2, 0.8, 1),
    64: (0, 0, 1, 1),
    128: (0.2, 0, 0.8, 1),
    256: (0.4, 0, 0.6, 1),
    512: (0.6, 0, 0.4, 1),
    1024: (0.8, 0, 0.2, 1),
    2048: (1, 0, 0, 1)
}

class Tile(Button):
    '''
    customised Tile class with property value
    when changing value, change text and color at the same time
    '''
    def __init__(self, value=0, **kwargs):
        Label.__init__(self, **kwargs)
        self.font_size = 48
        self.value = value
        self.background_disabled_normal = self.background_normal

    def set_value(self, value):
        self._value = value
        if value == 0:
            self.text = ''
        else:
            self.text = str(value)
        if value in tile_color_map:
            t = 0.1 if value > 0 else 0
            anim = Animation(background_color = tile_color_map.get(value), duration=t)
            anim.start(self)

    def get_value(self):
        return self._value

    value = property(get_value, set_value)

class Menu(Screen):
    def __init__(self, **kwargs):
        Screen.__init__(self, **kwargs)
        self.layout = BoxLayout(orientation='vertical')
        title = Label(text='2048', font_size=48)
        startButton = Button(text='Start', on_press=self.start_game, font_size=48)
        
        self.layout.add_widget(title)
        self.layout.add_widget(startButton)
        self.add_widget(self.layout)
    
    def start_game(self, value):
        '''slide to game screen and start game'''
        self.manager.transition.direction = 'left'
        self.manager.current = 'game'

class Game(Screen):
    def __init__(self, **kwargs):
        Screen.__init__(self, **kwargs)
        self.layout = BoxLayout(orientation='vertical')
        self.top_bar = BoxLayout(orientation='horizontal', size_hint_y=0.2)
        self.grid = GridLayout(cols=4, padding=2)
        self.score = 0
        self.over = False
        self.touch_initial = (0, 0)
        self.matrix = np.zeros((4, 4), np.int)
        self.tiles = []       
        for i in range(4):
            for j in range(4):
                if j == 0:
                    self.tiles.append([])
                self.tiles[i].append(Tile(value=0, disabled=True))
                self.grid.add_widget(self.tiles[i][j])
        
        # top bar
        restartButton = Button(text='Restart', on_press=self.restart, font_size=24, size_hint_x=0.5)
        quitButton = Button(text='Quit', on_press=self.quit, font_size=24, size_hint_x=0.5)
        saveButton = Button(text='Save', on_press=self.save, font_size=24, size_hint_x=0.5)
        loadButton = Button(text='Load', on_press=self.load, font_size=24, size_hint_x=0.5)
        self.scoreLabel = Label(text=str(self.score), font_size=24)
        self.top_bar.add_widget(quitButton)
        self.top_bar.add_widget(restartButton)
        self.top_bar.add_widget(self.scoreLabel)
        self.top_bar.add_widget(saveButton)
        self.top_bar.add_widget(loadButton)
        
        # swipe control
        self.grid.bind(on_touch_down=self._touch_down)
        self.grid.bind(on_touch_up=self._touch_up)

        # keyboard control
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)   

        self.layout.add_widget(self.top_bar)
        self.layout.add_widget(self.grid)
        self.add_widget(self.layout)

        # initialize with two tiles
        self.add_tile()
        self.add_tile()

    def _touch_down(self, instance, touch):
        self.touch_initial = (touch.x, touch.y)

    def _touch_up(self, instance, touch):
        if not self.over:
            dx = touch.x - self.touch_initial[0]
            dy = touch.y - self.touch_initial[1]

            if abs(dx) >= abs(dy):
                if dx < -40:
                    self.move(3) # left
                elif dx > 40:
                    self.move(2) # right
            else:
                if dy < -40:
                    self.move(0) # down
                elif dy > 40:
                    self.move(1) # up
        return True
    
    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if not self.over:
            if keycode[1] == 'up':
                self.move(1)
            elif keycode[1] == 'down':
                self.move(0)
            elif keycode[1] == 'left':
                self.move(3)
            elif keycode[1] == 'right':
                self.move(2)
            return True

    def add_tile(self):
        '''randomly add one tile with number 2 or 4'''
        choices = np.array([2, 4])
        probabilities = np.array([0.9, 0.1])
        val = np.random.choice(choices, 1, p=probabilities)[0]

        empties = self.get_empty()
        empty_index = np.random.choice(empties.shape[0])
        empty = empties[empty_index]

        self.matrix[empty[0], empty[1]] = val
        self.over = self.is_over()
        self.update()
        
    def get_empty(self):
        '''retuen a 2d numpy array with locations of empty entries'''
        return np.argwhere(self.matrix == 0)

    def move(self, direction, trial=False):
        '''
        one move of the game.
        direction: 0, 1, 2, 3 represent down, up, right, left
        tiral: when True: trial mode, won't change the matrix
        return: whether changed, score of the move
        '''
        changed = False
        score = 0
        shift_dir = (direction + 1) % 2

        if direction <= 1:
            # up or down, split matrix into columns
            for y in range(4):
                col = self.matrix[:,y]
                (new_col, s) = self.shift(col, shift_dir)
                score += s
                if (new_col != col).any():
                    changed = True
                    if not trial:
                        self.matrix[:, y] = new_col

        else:
            # left or right, split matrix into rows
            for x in range(4):
                row = self.matrix[x,:]
                (new_row, s) = self.shift(row, shift_dir)
                score += s
                if (new_row != row).any():
                    changed = True
                    if not trial:
                        self.matrix[x,:] = new_row

        if not trial and changed:
            self.score += score
            self.add_tile()

        return (changed, score) 
        

    def shift(self, row, direction):
        '''
        shift the row and combine the rows
        direction: left if direction==0, right if direction==1
        return:output row, score
        '''
        if direction:
            row = np.flip(row)
        # shift
        shifted_row = np.zeros([4], np.int)
        i = 0
        for n in row:
            if n != 0:
                shifted_row[i] = n
                i += 1   
        # combine
        score = 0
        output = np.zeros([4], np.int)
        output_index = 0
        skip = False
        for i in range(3):
            if skip or shifted_row[i] == 0:
                skip = False
                continue
            output[output_index] = shifted_row[i]
            if shifted_row[i] == shifted_row[i+1]:
                output[output_index] += shifted_row[i+1]
                score += shifted_row[i] * 2
                skip = True
            output_index += 1
        
        if not skip:
            output[output_index] = shifted_row[-1]

        if direction:
            output = np.flip(output)

        return (output, score)     

    def update(self):
        '''update the labels'''
        for i in range(4):
            for j in range(4):
                self.tiles[i][j].value = self.matrix[i, j]

        if self.over:
            self.scoreLabel.text = 'Game Over\nScore: {}'.format(self.score)
            popup = Popup(title='Notification',
                          content=Label(text='Game Over\nScore: {}'.format(self.score), font_size=24),
                          size_hint=(0.4, 0.3))
            popup.open()
        else:
            self.scoreLabel.text = str(self.score)


    def is_over(self):
        '''check if the game is over by trying all possible movements'''
        if self.get_empty().size != 0:
            return False
        else:
            for dir in range(4):
                if self.move(dir, trial=True)[0] == True:
                    return False
            return True
        

    def restart(self, value):
        '''restart the game, bound to restart button'''
        self.score = 0
        self.over = False
        self.matrix = np.zeros((4, 4), np.int)
        for row in self.tiles:
            for tile in row:
                tile.value = 0

        self.add_tile()
        self.add_tile()

    def save(self, value):
        '''save the game'''
        if self.over:
            msg = 'You cannot save a game\n that is already over!'        
        else:
            try:
                archive = (self.score, self.matrix.tolist())
                pickle.dump(archive, open('save.p', 'wb'))
                msg = 'Saved Successfully!'
            except:
                msg = 'Error saving the game:('
        
        popup = Popup(title='Notification',
                    content=Label(text=msg, font_size=24),
                    size_hint=(0.4, 0.3))
        popup.open()

    def load(self, value):
        '''load saved game'''
        backup = self.matrix
        try:
            score, lmatrix = pickle.load(open('save.p', 'rb'))
            assert len(lmatrix) == 4
            assert len(lmatrix[0]) == 4
            self.matrix = np.array(lmatrix)
            self.score = score
            msg = 'Loaded successfully!'
        except:
            msg = 'Error loading saved game :('
            self.matrix = backup

        popup = Popup(title='Notification',
                    content=Label(text=msg, font_size=24),
                    size_hint=(0.4, 0.3))
        popup.open()

        self.over = self.is_over()
        self.update()

    def quit(self, value):
        '''move back to menu screen without resetting the game'''
        self.manager.transition.direction = 'right'
        self.manager.current = 'menu'


class GameApp(App):
    def build(self):
        sm = ScreenManager()
        menu = Menu(name='menu')
        game = Game(name='game')
        sm.add_widget(menu)
        sm.add_widget(game)
        sm.current = 'menu'
        return sm

GameApp().run()
