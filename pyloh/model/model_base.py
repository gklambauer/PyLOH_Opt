'''
Abstract classes which all models for classifying paired data should sub-class.

Created on 2011-03-31

@author: Andrew Roth

JointSNVMix-0.6.2
joint_snv_mix.classification.base.EMModelTrainer
joint_snv_mix.classification.base.PriorParser

================================================================================

Modified on 2013-07-29

@author: Yi Li
'''
import sys

from ConfigParser import ConfigParser

import numpy as np

from pyloh import constants
from pyloh.preprocess.data import Data
from pyloh.model.utils import get_copynumber_tumor, get_copynumber_tumor_num

class ProbabilisticModel(object):
    def __init__(self, allelenumber_max):
        self.allelenumber_max = allelenumber_max
        self.priors_parser = PriorParser()
        self.data = Data()
        self._init_components()

    def read_priors(self, priors_filename):
        raise NotImplemented

    def read_data(self, filename_base):
        self.data.read_data(filename_base)

    def preprocess(self):
        raise NotImplemented

    def run(self, idx_restart, restart_parameters, max_iters, stop_value):
        trainer = self.model_trainer_class(self.priors, self.data, idx_restart,
                                    restart_parameters, self.config_parameters, max_iters, stop_value)

        trainer.train()

        self.model_parameters = trainer.model_parameters

        self.log_likelihood = trainer.log_likelihood

    def write_parameters(self, filename_base):
        self.model_parameters.write_parameters(filename_base)

    def _init_components(self):
        raise NotImplemented

#JointSNVMix
class ModelTrainer(object):
    def __init__(self, priors, data, idx_restart, restart_parameters, config_parameters, max_iters, stop_value):
        self.priors = priors

        self.data = data

        self.idx_restart = idx_restart

        self.restart_parameters = restart_parameters

        self.config_parameters = config_parameters

        self.max_iters = max_iters

        self.stop_value = stop_value

        self.iters = 0

        self._init_components()

    def train(self):
        converged = False

        parameters = self.model_parameters.parameters
        priors = self.priors
        old_log_likelihood = self.model_likelihood.get_log_likelihood(parameters, priors)

        while converged == False:
            self._E_step()
            self._M_step()

            parameters = self.model_parameters.parameters
            new_log_likelihood = self.model_likelihood.get_log_likelihood(parameters, priors)

            if self.iters > 0:
                ll_change = (new_log_likelihood - old_log_likelihood) / np.abs(old_log_likelihood)
            else:
                ll_change = float('inf')

            self._print_running_info(new_log_likelihood, old_log_likelihood, ll_change)

            old_log_likelihood = new_log_likelihood

            if np.abs(ll_change) < self.stop_value:
                print "Stop value of EM iterations exceeded. Exiting training..."
                sys.stdout.flush()
                converged = True

            if self.iters >= self.max_iters:
                print "Maximum numbers of EM iterations exceeded. Exiting training..."
                sys.stdout.flush()
                converged = True

            self.iters += 1

        self.log_likelihood = new_log_likelihood

    def _E_step(self):
        self.latent_variables.update(self.model_parameters.parameters, self.iters)

    def _M_step(self):
        self.model_parameters.update(self.latent_variables.sufficient_statistics)

    def _print_running_info(self, new_log_likelihood, old_log_likelihood, ll_change):
        raise NotImplemented

    def _init_components(self):
        raise NotImplemented

class LatentVariables(object):
    def __init__(self, data, restart_parameters, config_parameters):
        self.data = data
        self.restart_parameters = restart_parameters
        self.config_parameters = config_parameters

    def update(self, parameters):
        raise NotImplemented

class ModelParameters(object):
    def __init__(self, priors, data, restart_parameters, config_parameters):
        self.priors = priors
        self.data = data
        self.restart_parameters = restart_parameters
        self.config_parameters = config_parameters

        self._init_parameters()

    def update(self, sufficient_statistics):
        raise NotImplemented

    def write_parameters(self, filename_base):
        raise NotImplemented

    def _init_parameters(self):
        raise NotImplemented

class ModelLikelihood(object):
    def __init__(self, data, restart_parameters, config_parameters):
        self.data = data
        self.restart_parameters = restart_parameters
        self.config_parameters = config_parameters

    def get_log_likelihood(self, parameters, priors):
        raise NotImplemented

#JointSNVMix
class PriorParser(object):
    def __init__(self):
        self.priors = {}

    def read_priors(self, priors_filename, allelenumber_max):
        self.parser = ConfigParser()
        self.parser.read(priors_filename)

        copynumber_tumor = get_copynumber_tumor(allelenumber_max)
        copynumber_tumor_num = get_copynumber_tumor_num(allelenumber_max)

        self.priors['omega'] = np.zeros(copynumber_tumor_num)

        for i, copynumber in enumerate(copynumber_tumor):
            self.priors['omega'][i] = self.parser.getfloat('omega', str(copynumber))
