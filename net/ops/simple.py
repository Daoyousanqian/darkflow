import tensorflow.contrib.slim as slim
from baseop import BaseOp
import tensorflow as tf

class reorg(BaseOp):
	def forward(self):
		inp = self.inp.out
		shape = inp.get_shape().as_list()
		_, h, w, c = shape
		s = self.lay.stride
		out = list()
		for i in range(h/s):
			row_i = list()
			for j in range(w/s):
				si, sj = s * i, s * j
				boxij = inp[:, si: si+s, sj: sj+s,:]
				flatij = tf.reshape(boxij, [-1,1,1,c*s*s])
				row_i += [flatij]
			out += [tf.concat(2, row_i)]
		self.out = tf.concat(1, out)

	def speak(self):
		args = [self.lay.stride] * 2
		msg = 'local flatten {}x{}'
		return msg.format(*args)

class route(BaseOp):
	def forward(self):
		routes = self.lay.routes
		routes_out = list()
		for r in routes:
			this = self.inp
			while this.lay.number != r:
				this = this.inp
				assert this is not None, \
				'Routing to non-existence {}'.format(r)
			routes_out += [this.out]	
		self.out = tf.concat(3, routes_out)

	def speak(self):
		msg = 'concat {}'
		return msg.format(self.lay.routes)


class select(BaseOp):
	"""a weird connected layer"""
	def forward(self):
		self.out = tf.nn.xw_plus_b(
			self.inp.out, 
			self.lay.w['weights'], 
			self.lay.w['biases'],
			name = self.scope)

	def speak(self):
		layer = self.lay
		args = [layer.inp, layer.out]
		args += [layer.activation]
		msg = 'select {} x {}  {}'
		return msg.format(*args)


class connected(BaseOp):
	def forward(self):
		self.out = tf.nn.xw_plus_b(
			self.inp.out,
			self.lay.w['weights'], 
			self.lay.w['biases'], 
			name = self.scope)

	def speak(self):
		layer = self.lay
		args = [layer.inp, layer.out]
		args += [layer.activation]
		msg = 'full {} x {}  {}'
		return msg.format(*args)


class flatten(BaseOp):
	def forward(self):
		temp = tf.transpose(
			self.inp.out, [0,3,1,2])
		self.out = slim.flatten(
			temp, scope = self.scope)

	def speak(self): return 'flatten'


class softmax(BaseOp):
	def forward(self):
		self.out = tf.nn.softmax(self.inp.out)

	def speak(self): return 'softmax()'


class avgpool(BaseOp):
	def forward(self):
		self.out = tf.reduce_mean(
			self.inp.out, [1, 2], 
			name = self.scope
		)

	def speak(self): return 'avgpool()'


class dropout(BaseOp):
	def forward(self):
		self.out = tf.nn.dropout(
			self.inp.out, 
			self.lay.h['pdrop'], 
			name = self.scope
		)

	def speak(self): return 'drop()'


class crop(BaseOp):
	def forward(self):
		self.out =  self.inp.out * 2. - 1.

	def speak(self):
		return 'centralize to (-1, 1)'


class maxpool(BaseOp):
	def forward(self):
		self.out = tf.nn.max_pool(
			self.inp.out, padding = 'SAME',
	        ksize = [1] + [self.lay.ksize]*2 + [1], 
	        strides = [1] + [self.lay.stride]*2 + [1],
	        name = self.scope
	    )
	
	def speak(self):
		l = self.lay
		return 'maxp {}x{} p={} _{}'.format(
			l.ksize, l.ksize, l.pad, l.stride)


class leaky(BaseOp):
	def forward(self):
		self.out = tf.maximum(
			.1 * self.inp.out, 
			self.inp.out, 
			name = self.scope
		)

	def verbalise(self): pass


class identity(BaseOp):
	def __init__(self, inp):
		self.inp = None
		self.out = inp