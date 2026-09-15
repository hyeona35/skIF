const {SkifClient}=require('./sdk');
const c=new SkifClient('http://localhost:1','x');
if(c.base!=='http://localhost:1')process.exit(1);
if(typeof c.recommend!=='function' || typeof c.teamPlan!=='function')process.exit(1);
console.log('node sdk ok');
