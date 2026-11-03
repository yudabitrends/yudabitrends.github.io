const assert = require('node:assert/strict');
const {model} = require('../docs/assets/book-lab.js');
let checks=0;
function near(a,b,message){assert.ok(Math.abs(a-b)<1e-11,message+': '+a+' != '+b);}
for(let angle=-60;angle<=120;angle+=0.5){
  const result=model(angle), d=(30-angle)*Math.PI/180;
  near(result.mean[0],0,'mean');near(result.mean[1],0,'mean');
  near(result.variance[0],1,'variance');near(result.variance[1],1,'variance');
  near(result.covariance,0,'rotation must preserve zero covariance');
  near(result.kurtosis[0],-2+Math.sin(2*d)**2,'analytic kurtosis');
  near(result.kurtosis[1],result.kurtosis[0],'symmetric components');
}
checks++;
for(const angle of [-60,30,120]) assert.equal(model(angle).recovered,true);
for(const angle of [0,29,31,75]) assert.equal(model(angle).recovered,false);
model(30).output.forEach((p,i)=>p.forEach((v,j)=>near(v,model(30).source[i][j],'inverse rotation')));
checks++;
const y=model(75).output;
const pA=y.filter(p=>Math.abs(p[0])>1e-10).length/4;
const pB=y.filter(p=>Math.abs(p[1])>1e-10).length/4;
const pAB=y.filter(p=>Math.abs(p[0])>1e-10&&Math.abs(p[1])>1e-10).length/4;
near(pA,0.5,'nonzero marginal');near(pB,0.5,'nonzero marginal');near(pAB,0,'joint event');assert.notEqual(pAB,pA*pB);
checks++;
for(const bad of [NaN,Infinity,-Infinity,'30',null]) assert.throws(()=>model(bad),TypeError);
const a=model(0);a.source[0][0]=100;near(model(0).source[0][0],-1,'model must not expose mutable shared data');
checks++;
console.log('PASS '+checks+' beginner lab checks: exact moments across 361 angles, inverse/ambiguities, dependence counterexample, invalid input and state isolation.');
