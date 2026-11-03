/* Exact four-point teaching model; not an ICA estimator. */
(function () {
  'use strict';
  var source = [[-1,-1],[-1,1],[1,-1],[1,1]];
  function rotate(points, degrees) {
    var r=degrees*Math.PI/180, c=Math.cos(r), s=Math.sin(r);
    return points.map(function(p){return [c*p[0]-s*p[1],s*p[0]+c*p[1]];});
  }
  function model(undoDegrees) {
    if (typeof undoDegrees!=='number' || !Number.isFinite(undoDegrees)) throw new TypeError('Angle must be finite.');
    var observed=rotate(source,30), output=rotate(observed,-undoDegrees);
    var mean=[0,0], variance=[0,0], fourth=[0,0], covariance=0;
    output.forEach(function(p){mean[0]+=p[0]/4;mean[1]+=p[1]/4;});
    output.forEach(function(p){var a=p[0]-mean[0],b=p[1]-mean[1];variance[0]+=a*a/4;variance[1]+=b*b/4;fourth[0]+=a*a*a*a/4;fourth[1]+=b*b*b*b/4;covariance+=a*b/4;});
    return {source:source.map(function(p){return p.slice();}),observed:observed,output:output,mean:mean,variance:variance,covariance:covariance,kurtosis:fourth.map(function(v,i){return v/(variance[i]*variance[i])-3;}),recovered:Math.abs(Math.sin(2*(30-undoDegrees)*Math.PI/180))<1e-10};
  }
  if (typeof module!=='undefined' && module.exports) module.exports={model:model};
  if (typeof document==='undefined') return;
  var lab=document.getElementById('mixing-lab');
  if (!lab) return;
  var input=document.getElementById('lab-angle');
  function numeric(x){return (Math.abs(x)<1e-10?0:x).toFixed(3);}
  function render() {
    var angle=Number(input.value), state=model(angle);
    document.getElementById('lab-angle-value').textContent=angle+'°';
    input.setAttribute('aria-valuetext',angle+' degrees / 度');
    state.output.forEach(function(p,i){
      var group=document.querySelector('#lab-output [data-point="'+i+'"]');
      var circle=group.querySelector('circle'), text=group.querySelector('text');
      circle.setAttribute('cx',110+50*p[0]); circle.setAttribute('cy',110-50*p[1]);
      text.setAttribute('x',117+50*p[0]); text.setAttribute('y',106-50*p[1]);
    });
    document.getElementById('lab-covariance').textContent=numeric(state.covariance);
    document.getElementById('lab-kurtosis').textContent=numeric(state.kurtosis[0]);
    var status=document.getElementById('lab-status');
    status.querySelector('[lang="en"]').textContent=state.recovered?'Separated, allowing source swaps and sign changes.':'Still a mixture. Covariance alone does not reveal that.';
    status.querySelector('[lang="zh-CN"]').textContent=state.recovered?'已分离；允许源的顺序交换和符号翻转。':'仍然是混合；仅看协方差看不出来。';
    lab.dataset.recovered=String(state.recovered);
  }
  input.disabled=false;
  input.addEventListener('input',render);
  lab.querySelectorAll('[data-lab-angle]').forEach(function(button){button.disabled=false;button.addEventListener('click',function(){input.value=button.dataset.labAngle;render();});});
  render();
})();
