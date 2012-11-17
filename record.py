#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gtk
import subprocess

class Assistant:

	g_device = ''

	def __init__(self):
		self.capturing = False
		assistant = gtk.Assistant()
		self.assistant = assistant

		f = open( '/proc/asound/cards', 'r' );
		cards = {}
		for c in f.read().split('\n'):
			try:
				dev  = int(c.lstrip().split(' ')[0])
				name = c.split(']: ')[1]
				cards[dev] = name
			except:
				pass
		f.close()

		output = subprocess.Popen( [ 'xrandr', '-q' ], 
				stdin=subprocess.PIPE, stdout=subprocess.PIPE ).communicate()[0]
		resolutions = []
		for line in output.split( '\n' ):
			try:
				if line.startswith( 'Screen' ):
					res = line.split(',')[1].strip().split(' ')
					resolutions += [ "%sx%s+0+0" % (res[1], res[3]) ]
				elif line.find( ' connected ' ) > 0:
					resolutions += [ line.split(' ')[2] ]
			except:
				pass

		assistant.connect("close", self.button_pressed, "Close")
		assistant.connect("cancel", self.button_pressed, "Cancel")

		vbox = gtk.VBox()
		vbox.set_border_width(5)
		page = assistant.append_page(vbox)
		assistant.set_page_title(vbox, "Page 1: Intro")
		assistant.set_page_type(vbox, gtk.ASSISTANT_PAGE_INTRO)
		label = gtk.Label('Screen recording for Opencast Matterhorn…')
		label.set_line_wrap(True)
		vbox.pack_start(label, True, True, 0)
		assistant.set_page_complete(vbox, True)


		table = gtk.Table( 5, 2)
		table.set_col_spacings(3)
		assistant.append_page(table)
		assistant.set_page_title(table, "Page 2: Select options")
		assistant.set_page_type(vbox, gtk.ASSISTANT_PAGE_CONTENT)
		# Device selection
		label = gtk.Label("Select device for audio input:")
		self.cardchooser = gtk.combo_box_new_text() 
		for d,n in cards.items():
			self.cardchooser.append_text( str(d) + ': ' + n )
		self.cardchooser.append_text( 'pulse' )
		self.cardchooser.set_active(0)
		table.attach( label, 0, 1, 0, 1)
		table.attach( self.cardchooser, 1, 2, 0, 1)
		# Rregion
		label = gtk.Label("Region to capture:")
		#self.regionentry = gtk.Entry()
		#self.regionentry.set_text( "1920x1200+0+0" )
		self.regionentry = gtk.Combo()
		self.regionentry.set_popdown_strings( resolutions )
		table.attach( label, 0, 1, 1, 2)
		table.attach( self.regionentry, 1, 2, 1, 2)
		# Output file
		label = gtk.Label("select output file:")
		#self.filechooserbutton = gtk.FileChooserButton("Select A File", None)
		self.filechooserbutton = gtk.Entry()
		table.attach( label, 0, 1, 2, 3)
		table.attach( self.filechooserbutton, 1, 2, 2, 3)
		# Audio codec
		label = gtk.Label("Select audio codec:")
		self.acodecchooser = gtk.combo_box_new_text() 
		for codec in ['flac', 'libmp3lame', 'libvorbis', 'vorbis', 'aac']:
			self.acodecchooser.append_text( codec )
		self.acodecchooser.set_active(0)
		table.attach( label, 0, 1, 3, 4)
		table.attach( self.acodecchooser, 1, 2, 3, 4)
		# Video codec
		label = gtk.Label("Select video codec:")
		self.vcodecchooser = gtk.combo_box_new_text() 
		for codec in ['mpeg2video', 'libtheora', 'theora', 'vp8', 'libx264', 'libxvid', 'ljpeg', 'flv']:
			self.vcodecchooser.append_text( codec )
		self.vcodecchooser.set_active(0)
		table.attach( label, 0, 1, 4, 5)
		table.attach( self.vcodecchooser, 1, 2, 4, 5)
		# page complete
		assistant.set_page_complete(table, True)
        
		vbox = gtk.VBox()
		vbox.set_border_width(5)
		assistant.append_page(vbox)
		assistant.set_page_title(vbox, "Page 3: Start capturing")
		assistant.set_page_type(vbox, gtk.ASSISTANT_PAGE_PROGRESS)
		self.capturebutton = gtk.Button('Start capturing…')
		vbox.pack_start(self.capturebutton, False, False, 0)
		self.capturebutton.connect( 'clicked', self.capture )


		vbox = gtk.VBox()
		vbox.set_border_width(5)
		assistant.append_page(vbox)
		assistant.set_page_title(vbox, "Page 4: The Finale")
		assistant.set_page_type(vbox, gtk.ASSISTANT_PAGE_SUMMARY)
		label = gtk.Label("TODO: Upload to Opencast Matterhorn…")
		label.set_line_wrap(True)
		vbox.pack_start(label, True, True, 0)
		assistant.set_page_complete(vbox, True)

		assistant.show_all()

	def capture(self, w):
		if not self.capturing:
			commandline = ('ffmpeg -f alsa -ac 2 -i hw:%s -f x11grab '
				'-s %s -r 30 -i :0.0+%s,%s -acodec %s '
				'-vcodec %s -b 10000k -threads 1 -y %s.mkv'
				% (
					self.cardchooser.get_active_text().split(':')[0],
					self.regionentry.entry.get_text().split('+')[0],
					self.regionentry.entry.get_text().split('+')[1],
					self.regionentry.entry.get_text().split('+')[2],
					self.acodecchooser.get_active_text(),
					self.vcodecchooser.get_active_text(),
					#self.filechooserbutton.get_filename()
					self.filechooserbutton.get_text()
					))
			print( commandline )
			print(  )
			print( '---' )
			self.capturebutton.set_label('Stop capturing…')
			self.capturing = True
			self.ffmpegprocess = subprocess.Popen( commandline.split(), 
					stdin=subprocess.PIPE, stdout=subprocess.PIPE )
		else:
			self.capturebutton.hide()
			self.ffmpegprocess.communicate('q')
			self.assistant.set_page_complete(self.assistant.get_nth_page(
				self.assistant.get_current_page()), True)


	def choosing_card( self, w):
		index = w.get_active() 
		text  = w.get_model()[index][0]
		self.g_device = int(text.split(':')[0])


	def button_pressed(self, assistant, button):
		print "%s button pressed" % button
		gtk.main_quit()


if __name__ == '__main__':
	Assistant()
	gtk.main()
