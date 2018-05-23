#!/usr/bin/env python
# -*- coding: utf-8 -*-


#-- General imports --#
import os
import requests
from pprint import pprint
from random import randint
import json

#-- 3rd party imports --#
from rasa_core.agent import Agent
from rasa_core.policies.keras_policy import KerasPolicy
from rasa_core.policies.memoization import MemoizationPolicy
from rasa_core.channels import UserMessage
from rasa_core.channels.console import ConsoleInputChannel
from telegram import ChatAction

#-- local imports --#
from Fibot.NLP.nlu import NLU_unit


class Query_answer_unit(object):

	""" This object contains tools to answer in natural language any message Fib related

	Attributes:
		nlu(:class:`Fibot.NLP.nlu.NLU_unit`): Object that interprets queries
		training_data_file(:obj:`str`): String indicating the path to the stories markdown file
		model_path(:obj:`str`): String indicating where the dialog model is
		agent_ca(:class:`rasa_core.agent.Agent`): Agent capable of handling any incoming messages in catalan
		agent_es(:class:`rasa_core.agent.Agent`): Agent capable of handling any incoming messages in spanish
		agent_en(:class:`rasa_core.agent.Agent`): Agent capable of handling any incoming messages in english
	"""
	def __init__(self):
		self.nlu = NLU_unit()
		self.training_data_file = './Fibot/NLP/core/stories.md'
		self.domain_path = './Fibot/NLP/core/domain.yml'
		self.model_path = './models/dialogue'
		self.agent_ca =  Agent(self.domain_path,
			                  policies=[MemoizationPolicy(), KerasPolicy()])
		self.agent_es =  Agent(self.domain_path,
							  policies=[MemoizationPolicy(), KerasPolicy()])
		self.agent_en =  Agent(self.domain_path,
							  policies=[MemoizationPolicy(), KerasPolicy()])
		self.agent_ca.toggle_memoization(activate = True)
		self.agent_es.toggle_memoization(activate = True)
		self.agent_en.toggle_memoization(activate = True)

	"""
		Parameters:
			train (:obj:`bool`): Specifies if the agents have to be trained
		This function loads the model into the agents, and trains them if necessary
	"""
	def load(self, trainNLG=False, trainNLU=False):
		self.nlu.load(trainNLU)
		if trainNLG: self.train()
		self.agent_ca = Agent.load(self.model_path,
				interpreter = self.nlu.interpreter_ca)
		self.agent_es = Agent.load(self.model_path,
				interpreter = self.nlu.interpreter_es)
		self.agent_en = Agent.load(self.model_path,
				interpreter = self.nlu.interpreter_en)

	"""
		Parameters:
			augmentation_factor (:obj:`int`): augmentation factor for the training
			max_history (:obj:`int`): max_history factor for the training
			epochs (:obj:`int`): epochs (steps) for the training
			batch_size (:obj:`int`): batch_size for the training
			validation_split (:obj:`int`): validation_split factor for the error calculation

		This function trains the agents and saves the models in the dialog's model path
	"""
	def train(self, augmentation_factor=250, max_history=5, epochs=500, batch_size=500, validation_split=0.33):
		self.agent_es.train(self.training_data_file,
			augmentation_factor=augmentation_factor,
			max_history=max_history,
			epochs=epochs,
		 	batch_size=batch_size,
			validation_split=validation_split
		)
		self.agent_es.persist(self.model_path)

	"""
		Parameters:
			augmentation_factor (:obj:`int`): augmentation factor for the training
			max_history (:obj:`int`): max_history factor for the training
			epochs (:obj:`int`): epochs (steps) for the training
			batch_size (:obj:`int`): batch_size for the training
			validation_split (:obj:`int`): validation_split factor for the error calculation

		This function makes it possible to generate new stories manually.
	"""
	def train_manual(self, augmentation_factor=50, max_history=2, epochs=500, batch_size=50, validation_split=0.2):
		self.agent_es.train_online(self.training_data_file,
			input_channel = ConsoleInputChannel(),
			augmentation_factor=augmentation_factor,
			max_history=max_history,
			epochs=epochs,
		 	batch_size=batch_size,
			validation_split=validation_split
		)

	"""
		Parameters:
			message (:obj:`str`): the incoming message from some user
			sender_id(:obj:`str`): The id (chat_id) of the sender of the messages
			language(:obj:`str`): The language of the sender ('ca', 'es' or 'en')
			debug(:obj:`bool`): Boolean value indicating wether it has to output model's response

		This function returns the response from the agent using the actions
		defined in Fibot/NLP/core/actions.py
	"""
	def get_response(self, message, sender_id=UserMessage.DEFAULT_SENDER_ID, language = 'es', debug=True):
		confidence = self.nlu.get_intent(message, language)['confidence']
		if debug:
			print("\n\nDEBUGGING INFO:")
			print("__________________________________________")
			print("Interpreter understood the following intent:")
			pprint(self.nlu.get_intent(message, language))
			print("And the following entities:")
			pprint(self.nlu.get_entities(message, language))
			print("\n\n")
		if confidence < 0.5:
			with open('./Data/error_responses.json', 'rb') as fp:
				messages = json.load(fp)['not_understand']
			return [messages[language][randint(0,len(messages[language])-1)]]
		if language == 'ca':
			print('Getting response in catalan')
			return self.agent_ca.handle_message(message, sender_id=sender_id)
		elif language == 'es':
			print('Getting response in spanish')
			return self.agent_es.handle_message(message, sender_id=sender_id)
		else:
			print('Getting response in english')
			return self.agent_en.handle_message(message, sender_id=sender_id)
