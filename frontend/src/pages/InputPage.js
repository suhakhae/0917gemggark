// src/pages/InputPage.js 
import React, { useState, useEffect } from 'react';
import { Box, Typography, Slider, Button, IconButton, Select, MenuItem, FormControl, InputLabel, TextField, Chip, Grid, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, CircularProgress, Divider } from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import axios from 'axios';

const gemTypes = ["안정", "견고", "불변", "침식", "왜곡", "붕괴"];
const gradeOrder = ['고급', '희귀', '영웅'];
const pointOptions = [1, 2, 3, 4, 5]; // <<< 2. 보유 젬 선택 옵션

const InputPage = ({ setPageState, setTaskId }) => {
  const [gemPrices, setGemPrices] = useState(null);
  const [pricesLoading, setPricesLoading] = useState(true);
  const [pricesError, setPricesError] = useState(null);
  const [cores, setCores] = useState([]);
  const [nextCoreId, setNextCoreId] = useState(1);
  const [heldGems, setHeldGems] = useState([]);
  const [nextGemId, setNextGemId] = useState(1);
  const [crystalPrice, setCrystalPrice] = useState(8000);
  const [simulations, setSimulations] = useState(100);

  useEffect(() => {
    const fetchGemPrices = async () => {
      try {
        setPricesLoading(true);
        const response = await axios.get('http://localhost:8000/markets/gems');
        setGemPrices(response.data);
        setPricesError(null);
      } catch (error) {
        console.error("젬 시세 로딩 실패:", error);
        setPricesError("실시간 젬 시세를 불러오는 데 실패했습니다.");
      } finally {
        setPricesLoading(false);
      }
    };
    fetchGemPrices();
  }, []);

  // <<< 1. 코어 추가 함수에 개수 제한 로직 추가
  const addCore = () => {
    if (cores.length < 6) {
      setCores([...cores, { id: nextCoreId, type: '질서', grade: '고대' }]);
      setNextCoreId(nextCoreId + 1);
    } else {
      alert("코어는 최대 6개까지만 추가할 수 있습니다.");
    }
  };
  const removeCore = (id) => setCores(cores.filter(core => core.id !== id));
  const handleCoreChange = (id, field, value) => { setCores(cores.map(core => core.id === id ? { ...core, [field]: value } : core)); };
  
  const addHeldGem = () => { setHeldGems([...heldGems, { id: nextGemId, name: '안정', core_point: 5, efficiency: 5 }]); setNextGemId(nextGemId + 1); };
  const removeHeldGem = (id) => setHeldGems(heldGems.filter(gem => gem.id !== id));
  const handleHeldGemChange = (id, field, value) => { const parsedValue = (field === 'core_point' || field === 'efficiency') ? parseInt(value, 10) : value; setHeldGems(heldGems.map(gem => gem.id === id ? { ...gem, [field]: parsedValue } : gem)); };
  
  const handleCrystalChange = (event, newValue) => setCrystalPrice(newValue);
  const handleSimulationsChange = (event, newValue) => setSimulations(newValue);
  
  const handleOptimizeClick = async () => {
    const formattedCores = { "질서": cores.filter(c => c.type === '질서').map(c => c.grade), "혼돈": cores.filter(c => c.type === '혼돈').map(c => c.grade) };
    const formattedHeldGems = heldGems.map(({ id, name, ...rest }) => { const isOrderGem = ["안정", "견고", "불변"].includes(name); const prefix = isOrderGem ? "질서의 젬 : " : "혼돈의 젬 : "; return { ...rest, name: `${prefix}${name}` }; });
    const requestData = { cores: formattedCores, held_gems: formattedHeldGems, blue_crystal_price: crystalPrice, simulations_per_gem: simulations };
    try {
      const response = await axios.post('http://localhost:8000/optimize', requestData);
      const { task_id } = response.data;
      if (task_id) { setTaskId(task_id); setPageState('loading'); } 
      else { alert("작업 ID를 받아오는데 실패했습니다."); }
    } catch (error) { console.error("API 요청 실패:", error); if (error.response) { alert(`최적화 실패: ${error.response.data.detail}`); } else { alert("서버에 연결할 수 없습니다. 백엔드 서버가 실행 중인지 확인해주세요."); } setPageState('input'); }
  };

  const renderPriceTable = (title, filterKeyword) => (
      <TableContainer component={Paper}><Typography variant="h6" sx={{ p: 2, textAlign: 'center' }}>{title}</Typography><Table size="small"><TableHead><TableRow><TableCell sx={{ width: '10%' }}>아이콘</TableCell><TableCell>아이템 이름</TableCell><TableCell align="right">최저가 (Gold)</TableCell></TableRow></TableHead><TableBody>{Object.entries(gemPrices).filter(([name]) => name.includes(filterKeyword)).sort(([aName], [bName]) => { const aGrade = gradeOrder.findIndex(g => aName.includes(g)); const bGrade = gradeOrder.findIndex(g => bName.includes(g)); if (aGrade !== bGrade) { return aGrade - bGrade; } return aName.localeCompare(bName); }).map(([name, price]) => (<TableRow key={name}><TableCell></TableCell><TableCell>{name}</TableCell><TableCell align="right">{price ? price.toLocaleString() : 'N/A'}</TableCell></TableRow>))}</TableBody></Table></TableContainer>
  );

  return (
    <Box sx={{ flexGrow: 1, p: 2 }}>
      { }
      <Paper elevation={3} sx={{ p: 2, mb: 3 }}><Typography variant="h5" gutterBottom sx={{ textAlign: 'center' }}>실시간 젬 시세</Typography><Box sx={{ display: 'flex', justifyContent: 'center', my: 2 }}>{pricesLoading && <CircularProgress />}{pricesError && <Typography color="error">{pricesError}</Typography>}</Box>{gemPrices && (<Grid container spacing={2} justifyContent="center"><Grid item xs={12} md={5}>{renderPriceTable('질서의 젬', '질서')}</Grid><Grid item xs={12} md={5}>{renderPriceTable('혼돈의 젬', '혼돈')}</Grid></Grid>)}</Paper>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={7}>
          <Paper elevation={3} sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom>1. 코어 구성</Typography>
            <Box sx={{ mb: 2 }}>{cores.map((core) => (<Box key={core.id} sx={{ display: 'flex', alignItems: 'center', mb: 1 }}><FormControl sx={{ m: 1, minWidth: 120 }}><InputLabel>타입</InputLabel><Select value={core.type} label="타입" onChange={(e) => handleCoreChange(core.id, 'type', e.target.value)}><MenuItem value="질서">질서</MenuItem><MenuItem value="혼돈">혼돈</MenuItem></Select></FormControl><FormControl sx={{ m: 1, minWidth: 120 }}><InputLabel>등급</InputLabel><Select value={core.grade} label="등급" onChange={(e) => handleCoreChange(core.id, 'grade', e.target.value)}><MenuItem value="고대">고대</MenuItem><MenuItem value="유물">유물</MenuItem></Select></FormControl><IconButton aria-label="delete" onClick={() => removeCore(core.id)}><DeleteIcon /></IconButton></Box>))}</Box>
            {/* <<< 1. 코어 추가 버튼에 disabled 속성 추가 */}
            <Button variant="outlined" onClick={addCore} disabled={cores.length >= 6}>+ 코어 추가</Button>
            
            <Divider sx={{ my: 3 }} />

            <Typography variant="h6" gutterBottom>2. 보유 젬 (선택)</Typography>
            <Box sx={{ mb: 2 }}>
              {heldGems.map((gem) => (
                <Box key={gem.id} sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <FormControl sx={{ m: 1, minWidth: 120 }}><InputLabel>젬 타입</InputLabel><Select value={gem.name} label="젬 타입" onChange={(e) => handleHeldGemChange(gem.id, 'name', e.target.value)}>{gemTypes.map(type => <MenuItem key={type} value={type}>{type}</MenuItem>)}</Select></FormControl>
                  
                  {/* <<< 2. 보유 젬 입력을 TextField에서 Select로 변경 */}
                  <FormControl sx={{ m: 1, minWidth: 120 }}><InputLabel>코어 포인트</InputLabel><Select value={gem.core_point} label="코어 포인트" onChange={(e) => handleHeldGemChange(gem.id, 'core_point', e.target.value)}>{pointOptions.map(p => <MenuItem key={p} value={p}>{p}</MenuItem>)}</Select></FormControl>
                  <FormControl sx={{ m: 1, minWidth: 120 }}><InputLabel>효율</InputLabel><Select value={gem.efficiency} label="효율" onChange={(e) => handleHeldGemChange(gem.id, 'efficiency', e.target.value)}>{pointOptions.map(p => <MenuItem key={p} value={p}>{p}</MenuItem>)}</Select></FormControl>

                  <IconButton aria-label="delete" onClick={() => removeHeldGem(gem.id)}><DeleteIcon /></IconButton>
                </Box>
              ))}
            </Box>
            <Button variant="outlined" onClick={addHeldGem}>+ 보유 젬 추가</Button>
          </Paper>
        </Grid>

        { }
        <Grid item xs={12} md={5}><Paper elevation={3} sx={{ p: 2, height: '100%' }}><Typography variant="h6" gutterBottom>3. 시장 및 설정</Typography><Box sx={{ width: '90%', margin: 'auto', mt: 2 }}><Typography gutterBottom>블루 크리스탈 시세: {crystalPrice.toLocaleString()} Gold</Typography><Slider value={crystalPrice} onChange={handleCrystalChange} step={100} marks min={2000} max={20000} /><Box sx={{ mt: 3 }}><Typography gutterBottom>정밀도 (시뮬레이션 횟수): {simulations} 회</Typography><Typography variant="caption" color="text.secondary">(높을수록 계산 시간이 오래 걸립니다)</Typography><Slider value={simulations} onChange={handleSimulationsChange} step={50} marks min={50} max={1000} /><Chip label={`예상 시간: ${getEstimatedTime(simulations)}`} color="info" variant="outlined" size="small" /></Box></Box></Paper></Grid>
      </Grid>
      
      <Box sx={{ textAlign: 'center', mt: 3 }}>
        {/* <<< 1. 최적화 버튼에 disabled 속성 추가 */}
        <Button variant="contained" color="success" onClick={handleOptimizeClick} sx={{ padding: '15px 50px', fontSize: '18px' }} disabled={cores.length === 0}>
          최적화 시작하기
        </Button>
      </Box>
    </Box>
  );
};

const getEstimatedTime = (sims) => {
  if (sims <= 200) return "약 1분 이내";
  if (sims <= 500) return "약 1~3분";
  if (sims <= 800) return "약 3~5분";
  return "5분 이상";
};

export default InputPage;