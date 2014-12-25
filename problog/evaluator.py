from __future__ import print_function

from collections import defaultdict

from .core import LABEL_QUERY, LABEL_EVIDENCE_POS, LABEL_EVIDENCE_NEG, LABEL_EVIDENCE_MAYBE

import subprocess
import sys, os, tempfile

class Semiring(object) :
    
    def one(self) :
        raise NotImplementedError()
    
    def zero(self) :
        raise NotImplementedError()
        
    def plus(self, a, b) :
        raise NotImplementedError()

    def times(self, a, b) :
        raise NotImplementedError()

    def negate(self, a) :
        raise NotImplementedError()

    def value(self, a) :
        raise NotImplementedError()

    def normalize(self, a, Z) :
        raise NotImplementedError()
    
class SemiringProbability(Semiring) :

    def one(self) :
        return 1.0

    def zero(self) :
        return 0.0
        
    def plus(self, a, b) :
        return a + b
        
    def times(self, a, b) :
        return a * b

    def negate(self, a) :
        return 1.0 - a
                
    def value(self, a) :
        return float(a)

    def normalize(self, a, Z) :
        return a/Z

class SemiringSymbolic(Semiring) :
    
    def one(self) :
        return "1"
    
    def zero(self) :
        return "0"
        
    def plus(self, a, b) :
        if a == "0" :
            return b
        elif b == "0" :
            return a
        else :
            return "(%s + %s)" % (a,b)

    def times(self, a, b) :
        if a == "0" or b == "0" :
            return "0"
        elif a == "1" :
            return b
        elif b == "1" :
            return a
        else :
            return "%s*%s" % (a,b)

    def negate(self, a) :
        if a == "0" :
            return "1"
        elif a == "1" :
            return "0"
        else :
            return "(1-%s)" % a 

    def value(self, a) :
        return str(a)
        
    def normalize(self, a, Z) :
        if Z == "1" :
            return a
        else :
            return "%s / %s" % (a,Z)

class Evaluatable(object) :
    
    def _createEvaluator(self, semiring, weights) :
        raise NotImplementedError('Evaluatable._createEvaluator is an abstract method')
    
    def getEvaluator(self, semiring=None, evidence=None, weights=None) :
        if semiring == None :
            semiring = SemiringProbability()

        evaluator = self._createEvaluator(semiring, weights)

        for n_ev, node_ev in evaluator.getNames(LABEL_EVIDENCE_POS) :
            if evidence == None :
                evaluator.addEvidence( node_ev )
            else :
                value = evidence.get( n_ev, None )
                if value == True : 
                    evaluator.addEvidence( node_ev )
                elif value == False :
                    evaluator.addEvidence( -node_ev )

        for n_ev, node_ev in evaluator.getNames(LABEL_EVIDENCE_NEG) :
            if evidence == None :
                evaluator.addEvidence( -node_ev )
            else :
                value = evidence.get( n_ev, None )
                if value == True : 
                    evaluator.addEvidence( node_ev )
                elif value == False :
                    evaluator.addEvidence( -node_ev )

        if evidence != None :
            for n_ev, node_ev in evaluator.getNames(LABEL_EVIDENCE_MAYBE) :
                value = evidence.get( n_ev, None )
                if value == True : 
                    evaluator.addEvidence( node_ev )
                elif value == False :
                    evaluator.addEvidence( -node_ev )


        evaluator.propagate()
        return evaluator

    def evaluate(self, index=None, semiring=None, evidence=None, weights=None) :
        evaluator = self.getEvaluator(semiring, evidence, weights)
    
        if index == None :
            result = {}
            # Probability of query given evidence
            for name, node in evaluator.getNames(LABEL_QUERY) :
                w = evaluator.evaluate(node)    
                if w < 1e-6 : 
                    result[name] = 0.0
                else :
                    result[name] = w
            return result
        else :
            return evaluator.evaluate(node)
    
    



class Evaluator(object) :

    def __init__(self, formula, semiring) :
        self.formula = formula
        self.__semiring = semiring
        
        self.__evidence = []
        
    def _get_semiring(self) : return self.__semiring
    semiring = property(_get_semiring)
        
    def initialize(self) :
        raise NotImplementedError('Evaluator.initialize() is an abstract method.')
        
    def propagate(self) :
        raise NotImplementedError('Evaluator.propagate() is an abstract method.')
        
    def evaluate(self, index) :
        """Compute the value of the given node."""
        raise NotImplementedError('Evaluator.evaluate() is an abstract method.')
        
    def getZ(self) :
        """Get the normalization constant."""
        raise NotImplementedError('Evaluator.getZ() is an abstract method.')
        
    def addEvidence(self, node) :
        """Add evidence"""
        self.__evidence.append(node)
        
    def clearEvidence(self) :
        self.__evidence = []
        
    def iterEvidence(self) :
        return iter(self.__evidence)            
            

