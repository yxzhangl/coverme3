#include "config.h"
#include <cmath>
#include <utility>
#include <assert.h>
#include <map>
#include <set>
#include <algorithm>

static std::set<uint64_t> coveredInstIDs={}; //cover means boundary reached
static std::set<uint64_t> stagedInstIDs={}; //staged



enum DistanceStrategy {
  DIST_ABSOLUTE = 0,    // |x-y| (原始实现)
  DIST_RELATIVE,        // |x-y| / max(|x|,|y|,ε)
  DIST_LINEAR,          // |x-y| (与ABSOLUTE相同，保留接口)
  DIST_NORMALIZED,      // |x-y| / (1+|x|+|y|)
  DIST_LOG,             // |log(1+|x|) - log(1+|y|)|
  DIST_AUTO = 99        // 自适应选择
};

// 全局策略变量（默认原始策略）
static DistanceStrategy g_distance_strategy = DIST_ABSOLUTE;
static const double EPSILON = 1e-12;  // 数值安全阈值

// 【新增】C接口：供Python层设置策略
extern "C" void set_distance_strategy(int strategy) {
  if (strategy >= DIST_ABSOLUTE && strategy <= DIST_LOG) {
      g_distance_strategy = static_cast<DistanceStrategy>(strategy);
  } else if (strategy == DIST_AUTO) {
      g_distance_strategy = DIST_AUTO;
  }
  // 非法值保持当前策略不变
}

// 【新增】获取当前策略（调试用）
extern "C" int get_distance_strategy() {
  return static_cast<int>(g_distance_strategy);
}

// ============================================================================
// 【新增】各距离策略实现（静态内联，零开销抽象）
// ============================================================================

// 辅助：安全绝对值差
static inline double abs_diff(double x, double y) {
    return (x >= y) ? (x - y) : (y - x);
}

// 策略0/2: 绝对距离 |x-y|
static inline double dist_absolute(double x, double y) {
    return abs_diff(x, y);
}

// 策略1: 相对距离 |x-y|/max(|x|,|y|,ε)
static inline double dist_relative(double x, double y) {
    double diff = abs_diff(x, y);
    double max_val = std::fmax(std::fabs(x), std::fmax(std::fabs(y), EPSILON));
    return diff / max_val;
}

// 策略3: 归一化距离 |x-y|/(1+|x|+|y|) ∈ [0,1)
static inline double dist_normalized(double x, double y) {
    double diff = abs_diff(x, y);
    return diff / (1.0 + std::fabs(x) + std::fabs(y));
}

// 策略4: 对数距离 |log(1+|x|) - log(1+|y|)|
// 使用 log(1+|x|) 避免 x=0 时的 -inf 和负值问题
static inline double dist_log(double x, double y) {
    double lx = std::log1p(std::fabs(x));  // log(1+|x|), 数值更稳定
    double ly = std::log1p(std::fabs(y));
    return abs_diff(lx, ly);
}

// 策略99: 自适应策略（根据值域自动选择）
static inline double dist_auto(double x, double y) {
    double max_val = std::fmax(std::fabs(x), std::fabs(y));
    if (max_val < 1e-3) {
        // 极小值：用相对距离，避免绝对距离梯度消失
        return dist_relative(x, y);
    } else if (max_val < 1e4) {
        // 中等值：用归一化距离，保持梯度稳定
        return dist_normalized(x, y);
    } else {
        // 大值：用对数距离，压缩动态范围
        return dist_log(x, y);
    }
}

// ============================================================================
// 【替换】主 distance 函数：策略分发入口
// ============================================================================

static inline double distance(double x, double y) {
    // 数值安全检查
    if (std::isnan(x) || std::isnan(y) || std::isinf(x) || std::isinf(y)) {
        return 1e10;  // 返回大惩罚值，引导优化器远离无效区域
    }
    
    switch (g_distance_strategy) {
        case DIST_ABSOLUTE:
        case DIST_LINEAR:   // 两者实现相同
            return dist_absolute(x, y);
        case DIST_RELATIVE:
            return dist_relative(x, y);
        case DIST_NORMALIZED:
            return dist_normalized(x, y);
        case DIST_LOG:
            return dist_log(x, y);
        case DIST_AUTO:
        default:
            return dist_auto(x, y);
    }
}













extern long int __d;
extern double __r;
extern std::pair<int,int> lastBr;
static inline double distance(double x,double y);
extern std::set<std::pair<int,int>> explored;
extern std::set<std::pair<int,int>> passed_for_one_sample;
extern "C" void print_explored();
extern std::set<std::pair<int,int>> abandoned;
extern std::map<std::pair<int,int>,int> passStaged;
extern std::map<std::pair<int,int>,int> nPass;
extern "C" void print_passed_for_one_sample();
std::ostream& operator<< (std::ostream& os, std::pair<int,int> br){
  os<<"("<<br.first<<","<<br.second<<")";
  return os;
}

extern "C" void print_abandoned(){
  int ii=0;
  for(std::set<std::pair<int,int>>::iterator iter=abandoned.begin(); iter!=abandoned.end();++iter){
    std::cout << (ii==0?"":", ")<<ii<<":"<<"("<<iter->first<<","<<iter->second<<")" ;
    ii++;
  }
  std::cout<<std::endl;

}

static bool getTruth(double x,double y, int cmpID){

  bool truth=false;
  if (cmpID==32 || cmpID==1)
    truth=x==y;
  else if (cmpID==41 ||cmpID==5 || cmpID == 37)
    truth=x<=y;
  else if (cmpID==39 || cmpID==3 || cmpID==35)
    truth=x>=y;
  else if (cmpID==40 || cmpID==36 || cmpID==4)
    truth=x<y;
  else if (cmpID==2 || cmpID==38 ||cmpID==34)
    truth=x>y;
  else if (cmpID==33)
    truth = x!=y;

  else
    std::cerr  <<"\nWARNING !!!!!!!!!!!!!"<<"    cmpID = " << cmpID <<" not handled!\n\n";

  return truth;
}

static bool branchIsNone(std::pair<int,int> br){
  return br.first<0 || br.second<0;
}
static double inline amplifier_0630(double x){

  if (std::isinf(x)) std::cerr<<"Warning!!"<<"x is infinite\n";
  return 42*std::pow(x,4)+1;
}
int i_pen=0;
static void inline penalty_branchCoverage(double x,double y, uint64_t instID,int cmpID, int isInt){
  double __r_previous=__r;
  std::pair<int,int> br,br2;

  br=std::make_pair<int,int>(instID,getTruth(x,y,cmpID));
  br2=std::make_pair<int,int>(instID,not getTruth(x,y,cmpID));

  bool thisExplored=explored.count(br)>0
    || (passed_for_one_sample.count(br)>0 ||
        passed_for_one_sample.count(br2)>0 );
  bool thatExplored=explored.count(br2)>0
    || (passed_for_one_sample.count(br)>0 ||
        passed_for_one_sample.count(br2)>0 );

  if (thisExplored && thatExplored){
    DB ("quite early beause both children of instID = "<<instID<< " are explored");
    return;
  }
  double fn = amplifier_0630(nPass[br]);

  int choice;

  if (not thisExplored){
    choice=0;
    __r=0;
  }
  // if (not thisExplored){
  //   choice=0;
  //   __r=0;
  // }
  // else if (thatExplored){ //I don t want to go to the other branch
  //   choice = 1;
  //   //early quite
  //   return;
  //   //    __r = __r;
  // }
  // else{ //I would like to go there with guidance
  //   choice=2;
  //   __r = distance(x,y);
  // }


  else if (thatExplored){ //I don t want to go to the other branch
    assert (not thisExplored);
    choice = 1;
    __r=__r; //do nothing
  }
  else{ //I would like to go there with guidance
    choice=2;
    __r = distance(x,y) * fn;
  }




  DB("\t"<<i_pen<<": "<<"with instID = "<<instID <<"\n"<<
     "\t |" << "fn = "<<fn << "\n"<<
     "\t |" << "lhs, rhs, dist(lhs,rhs)  = "<< x <<","<< y<<","<< distance(x,y)<<"\n"<<
     "\t |" << "br,br2 <-lastBr : "<<br<<","<< br2<< " <- " <<lastBr<<"\n"<<
     "\t |" << "cmpID = "<<cmpID << "\n"<<
     "\t |" << "choice = "<<choice<<"\n"<<
     "\t |" << "__r =" << __r<<"\n"
     );
#ifdef DEBUG
  print_explored();
#endif
  i_pen++;

  lastBr=br;

  assert(br.second>=0 and br.first>=0);
  passed_for_one_sample.insert(br);
}

extern "C"
void __pen ( double x, double y , uint64_t instID,int cmpID, int isInt){
  //  penalty_min(x,y,instID);
  //    penalty_multiply(x,y,instID);
  penalty_branchCoverage(x,y,instID,cmpID,isInt);
}


//call at callBack time, do it before removeSingleSidedExploredBranch
extern "C" void addHardBranchAsExplored(){

  int instID=lastBr.first;
  int truth = lastBr.second;
  //in the case where lastBr=None (ie -1,-1 here), do not add it
  //This is possible because we are now alomost real-mao.
  if (instID==-1){return;}
  assert(lastBr.first>=0 and lastBr.second>=0);
  std::pair<int,int> lastBr2 = std::make_pair(instID, 1-truth);
  DB("**Abandonned: Branch that are the candidate to addHardBranchExplored..: "
     << " ("<< instID<< ","<<1-truth<<")"<<" \n");
  std::set<std::pair<int,int>> explored_afterAdd(explored);
// std::cout<<"***lastBr2="<<lastBr2<<" nPass ="<<nPass[lastBr2] <<", explored.count="<<explored.count(lastBr2)<<std::endl;
//  if (nPass[lastBr2]==0){
         if (explored.count(lastBr2)==0){
    assert(lastBr2.first>=0 and lastBr2.second>=0);
    explored_afterAdd.insert(lastBr2);
    abandoned.insert(lastBr2);
    DB("**Abandonned: Branch that are added to explored: "
       << " ("<< instID<< ","<<1-truth<<")"<<" \n");
  }
  explored=explored_afterAdd;

}

